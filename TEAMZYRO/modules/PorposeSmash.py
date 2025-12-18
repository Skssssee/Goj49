
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
    r = random.randint(1, 100)
    if r <= 40:
        return "Low"
    elif r <= 70:
        return "Medium"
    return "High"


# ─────────────────────────────
# PREVIEW HANDLER
# ─────────────────────────────

async def send_preview(message, mode):
    user_id = message.from_user.id
    now = datetime.utcnow()

    user = await user_collection.find_one({"id": user_id}) or {
        "id": user_id,
        "characters": [],
        "harem": [],
        "last_smash_time": None,
        "last_propose_time": None,
        "pending_action": None
    }

    # 🚫 BLOCK if pending action exists
    if user.get("pending_action"):
        return await message.reply_text(
            f"❌ You already have a **{user['pending_action']['mode'].upper()}** pending.\n"
            f"➡️ First cancel ❌ or confirm ✅ it."
        )

    last_time = user.get("last_smash_time" if mode == "smash" else "last_propose_time")
    cooldown = SMASH_COOLDOWN if mode == "smash" else PROPOSE_COOLDOWN

    if last_time and now - last_time < timedelta(minutes=cooldown):
        rem = timedelta(minutes=cooldown) - (now - last_time)
        m, s = divmod(int(rem.total_seconds()), 60)
        return await message.reply_text(
            f"⏳ Wait `{m}m {s}s` before using /{mode} again."
        )

    # 🎲 Dice animation
    await bot.send_dice(message.chat.id, "🎲")
    await asyncio.sleep(2)

    rolled_rarity = roll_rarity()

    char = await collection.aggregate([
        {"$match": {"img_url": {"$exists": True, "$ne": ""}}},
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not char:
        return await message.reply_text("❌ Character database empty.")

    char = char[0]

    # ✅ SAVE PENDING ACTION
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {
            "pending_action": {
                "mode": mode,
                "char_id": char.get("id"),
                "time": now
            }
        }},
        upsert=True
    )

    caption = (
        f"👤 **Name:** `{char.get('name','Unknown')}`\n"
        f"📺 **Anime:** `{char.get('anime','Unknown')}`\n"
        f"🆔 **ID:** `{char.get('id')}`\n"
        f"⭐ **Rarity:** `{rolled_rarity}`\n\n"
        f"❓ Do you want to **{mode.upper()}**?"
    )

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{mode}_{char['id']}_{rolled_rarity}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")
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

    char = await collection.find_one({"id": int(char_id)})
    if not char:
        return await cq.answer("Character not found", show_alert=True)

    success = random.randint(1, 100) <= RARITY_SUCCESS.get(rarity, 50)

    # ❌ FAILURE
    if not success:
        text = "❌ **Failed!**\nBetter luck next time."
        await cq.message.edit_caption(text)

    else:
        if mode == "smash":
            await user_collection.update_one(
                {"id": user_id},
                {
                    "$push": {"characters": char},
                    "$set": {"last_smash_time": now}
                },
                upsert=True
            )
            text = f"🔥 **SMASH SUCCESS!**\n`{char['name']}` added."

        else:
            await user_collection.update_one(
                {"id": user_id},
                {
                    "$push": {"harem": char},
                    "$set": {"last_propose_time": now}
                },
                upsert=True
            )
            text = f"💖 **PROPOSAL ACCEPTED!**\n`{char['name']}` joined your harem."

        await cq.message.edit_caption(text)

    # ✅ CLEAR PENDING ACTION
    await user_collection.update_one(
        {"id": user_id},
        {"$unset": {"pending_action": ""}}
    )

    await cq.answer("Done ✅")


# ─────────────────────────────
# CANCEL CALLBACK
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^cancel_action$"))
async def cancel_action(_, cq: CallbackQuery):
    user_id = cq.from_user.id

    await user_collection.update_one(
        {"id": user_id},
        {"$unset": {"pending_action": ""}}
    )

    await cq.message.edit_caption("❌ Action cancelled.")
    await cq.answer("Cancelled ❌")
