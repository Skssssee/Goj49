import asyncio
import random
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection


# ─────────────────────────────
# CONFIG
# ─────────────────────────────

SMASH_COOLDOWN = 10       # minutes
PROPOSE_COOLDOWN = 15     # minutes

RARITY_SUCCESS = {
    "Low": 80,
    "Medium": 60,
    "High": 40
}


# ─────────────────────────────
# RARITY ROLL (DISPLAY ONLY)
# ─────────────────────────────

def roll_rarity():
    roll = random.randint(1, 100)
    if roll <= 40:
        return "Low"
    elif roll <= 70:
        return "Medium"
    else:
        return "High"


# ─────────────────────────────
# PREVIEW HANDLER
# ─────────────────────────────

async def send_preview(message, mode):
    user_id = message.from_user.id
    now = datetime.utcnow()

    user = await user_collection.find_one({"id": user_id})
    if not user:
        user = {
            "id": user_id,
            "characters": [],
            "harem": [],
            "last_smash_time": None,
            "last_propose_time": None,
            "smash_streak": 0
        }
        await user_collection.insert_one(user)

    last_time = user.get("last_smash_time" if mode == "smash" else "last_propose_time")
    cooldown = SMASH_COOLDOWN if mode == "smash" else PROPOSE_COOLDOWN

    if last_time and now - last_time < timedelta(minutes=cooldown):
        rem = timedelta(minutes=cooldown) - (now - last_time)
        m, s = divmod(int(rem.total_seconds()), 60)
        return await message.reply_text(
            f"⏳ Wait `{m}m {s}s` before using /{mode} again."
        )

    await bot.send_dice(message.chat.id, "🎲")
    await asyncio.sleep(2)

    rolled_rarity = roll_rarity()

    character = await collection.aggregate([
        {"$match": {"img_url": {"$exists": True, "$ne": ""}}},
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not character:
        return await message.reply_text("❌ Character database is empty.")

    char = character[0]

    caption = (
        f"👤 **Name:** `{char.get('name','Unknown')}`\n"
        f"📺 **Anime:** `{char.get('anime','Unknown')}`\n"
        f"🆔 **ID:** `{char.get('id','N/A')}`\n"
        f"⭐ **Rarity:** `{rolled_rarity}`\n\n"
        f"❓ Do you want to **{mode.upper()}**?"
    )

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(
                "✅ Yes",
                callback_data=f"confirm_{mode}_{char.get('id','0')}_{rolled_rarity}"
            ),
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="cancel_action"
            )
        ]]
    )

    await message.reply_photo(
        photo=char["img_url"],
        caption=caption,
        reply_markup=keyboard
    )


# ─────────────────────────────
# COMMANDS
# ─────────────────────────────

@bot.on_message(filters.command("smash"))
async def smash_cmd(_, message):
    await send_preview(message, "smash")


@bot.on_message(filters.command("propose"))
async def propose_cmd(_, message):
    await send_preview(message, "propose")


# ─────────────────────────────
# CONFIRM CALLBACK
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^confirm_"))
async def confirm_action(_, cq: CallbackQuery):
    _, mode, char_id, rarity = cq.data.split("_")
    user_id = cq.from_user.id
    now = datetime.utcnow()

    char = await collection.find_one({"id": int(char_id)}) or await collection.find_one({})
    if not char:
        return await cq.answer("Character not found.", show_alert=True)

    success = random.randint(1, 100) <= RARITY_SUCCESS.get(rarity, 50)

    # ❌ FAILURE
    if not success:
        if mode == "smash":
            text = (
                "❌ **Smash Failed!**\n\n"
                "⚔️ The character resisted.\n"
                "💨 Try again later."
            )
        else:
            text = (
                "💔 **Proposal Failed**\n\n"
                "✨ The character wasn’t convinced."
            )
        await cq.message.edit_caption(text)
        await cq.answer()
        return

    # ✅ SUCCESS
    if mode == "smash":
        user = await user_collection.find_one({"id": user_id})
        streak = user.get("smash_streak", 0) + 1

        await user_collection.update_one(
            {"id": user_id},
            {
                "$push": {"characters": char},
                "$set": {
                    "last_smash_time": now,
                    "smash_streak": streak
                }
            },
            upsert=True
        )

        caption = (
            f"✨ **{char['name']}** has been smashed into submission!\n\n"
            f"• Added to your collection\n"
            f"• Power Level: 🔮 `{rarity}`\n\n"
            f"🔥 **Current Streak:** `{streak}`"
        )

    else:
        await user_collection.update_one(
            {"id": user_id},
            {
                "$push": {"harem": char},
                "$set": {"last_propose_time": now}
            },
            upsert=True
        )

        caption = (
            f"💫 **{char['name']}'s** eyes sparkled as they took your hand…\n"
            f"*\"I accept your heart\"* 💞\n\n"
            f"💞 **{char['name']}** has been added to your harem!"
        )

    await cq.message.edit_caption(caption)
    await cq.answer("✅ Success!")


# ─────────────────────────────
# CANCEL CALLBACK
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^cancel_action$"))
async def cancel_action(_, cq: CallbackQuery):
    await cq.message.edit_caption("❌ Action cancelled.")
    await cq.answer()
