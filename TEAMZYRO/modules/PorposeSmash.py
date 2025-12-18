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

SMASH_COOLDOWN = 10      # minutes (t)
PROPOSE_COOLDOWN = 15    # minutes (t)

RARITY_SUCCESS = {
    "Low": 80,
    "Medium": 60,
    "High": 40
}


def roll_rarity():
    r = random.randint(1, 100)
    if r <= 40:
        return "Low"
    elif r <= 70:
        return "Medium"
    return "High"


# ─────────────────────────────
# PREVIEW
# ─────────────────────────────

async def send_preview(message, mode):
    user_id = message.from_user.id
    now = datetime.utcnow()

    user = await user_collection.find_one({"id": user_id}) or {}

    pending_field = "pending_smash" if mode == "smash" else "pending_propose"
    cooldown_field = "last_smash_time" if mode == "smash" else "last_propose_time"
    cooldown = SMASH_COOLDOWN if mode == "smash" else PROPOSE_COOLDOWN

    # Pending check
    if user.get(pending_field):
        return await message.reply_text(
            f"❌ You already have a **{mode.upper()}** pending.\n"
            "➡️ First cancel ❌ or confirm ✅ it."
        )

    # Cooldown check
    last_time = user.get(cooldown_field)
    if last_time and now - last_time < timedelta(minutes=cooldown):
        rem = timedelta(minutes=cooldown) - (now - last_time)
        m, s = divmod(int(rem.total_seconds()), 60)
        return await message.reply_text(
            f"⏳ Wait `{m}m {s}s` before using /{mode} again."
        )

    await bot.send_dice(message.chat.id, "🎲")
    await asyncio.sleep(2)

    rarity = roll_rarity()

    char = await collection.aggregate([
        {"$match": {"img_url": {"$exists": True, "$ne": ""}}},
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not char:
        return await message.reply_text("❌ Character database empty.")

    char = char[0]

    await user_collection.update_one(
        {"id": user_id},
        {"$set": {
            pending_field: {
                "char": char,
                "rarity": rarity,
                "time": now
            }
        }},
        upsert=True
    )

    caption = (
        f"👤 **Name:** `{char['name']}`\n"
        f"📺 **Anime:** `{char['anime']}`\n"
        f"🆔 **ID:** `{char['id']}`\n"
        f"⭐ **Rarity:** `{rarity}`\n\n"
        f"Do you want to **{mode.upper()}**?"
    )

    kb = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{mode}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{mode}")
        ]]
    )

    await message.reply_photo(
        photo=char["img_url"],
        caption=caption,
        reply_markup=kb
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
# CONFIRM
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^confirm_"))
async def confirm_action(_, cq: CallbackQuery):
    mode = cq.data.split("_")[1]
    user_id = cq.from_user.id
    now = datetime.utcnow()

    pending_field = "pending_smash" if mode == "smash" else "pending_propose"
    cooldown_field = "last_smash_time" if mode == "smash" else "last_propose_time"

    user = await user_collection.find_one({"id": user_id}) or {}
    data = user.get(pending_field)

    if not data:
        return await cq.answer("No pending action.", show_alert=True)

    char = data["char"]
    rarity = data["rarity"]

    success = random.randint(1, 100) <= RARITY_SUCCESS.get(rarity, 50)

    # ❌ FAILURE
    if not success:
        if mode == "smash":
            await user_collection.update_one(
                {"id": user_id},
                {"$set": {"smash_streak": 0}}
            )
            await cq.message.edit_caption("❌ **Smash failed!**\nYour streak has been reset.")
        else:
            await cq.message.edit_caption("💔 **Proposal declined…**")

    # ✅ SUCCESS
    else:
        if mode == "smash":
            streak = user.get("smash_streak", 0) + 1
            await user_collection.update_one(
                {"id": user_id},
                {
                    "$push": {"characters": char},
                    "$set": {
                        "last_smash_time": now,
                        "smash_streak": streak
                    }
                }
            )

            await cq.message.edit_caption(
                f"✨ **{rarity.upper()} SMASH!**\n"
                f"You've smashed **{char['name']}** into submission!\n\n"
                "• Added to your collection\n"
                f"• Power Level: {rarity}\n\n"
                f"🔥 **Current streak:** {streak}"
            )

        else:
            await user_collection.update_one(
                {"id": user_id},
                {
                    "$push": {"harem": char},
                    "$set": {"last_propose_time": now}
                }
            )

            await cq.message.edit_caption(
                f"💫 **{char['name']}**'s eyes sparkled as they took your hand…\n"
                f"*\"I accept your heart\"* 💞\n\n"
                f"💞 **{char['name']}** has been added to your harem!"
            )

    await user_collection.update_one(
        {"id": user_id},
        {"$unset": {pending_field: ""}}
    )

    await cq.answer("Done ✅")


# ─────────────────────────────
# CANCEL
# ─────────────────────────────

@bot.on_callback_query(filters.regex("^cancel_"))
async def cancel_action(_, cq: CallbackQuery):
    mode = cq.data.split("_")[1]
    user_id = cq.from_user.id

    field = "pending_smash" if mode == "smash" else "pending_propose"

    await user_collection.update_one(
        {"id": user_id},
        {"$unset": {field: ""}}
    )

    await cq.message.edit_caption("❌ Action cancelled.")
    await cq.answer("Cancelled ❌")
