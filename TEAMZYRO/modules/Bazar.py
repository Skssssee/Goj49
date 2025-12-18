
import random
from datetime import datetime, timedelta

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection


# ─────────────────────────────────
# CONFIG
# ─────────────────────────────────

PRICES = {
    "low": 5,      # Common
    "medium": 1500,
    "high": 3000
}

BAZAR_LIMIT = 5
BAZAR_COOLDOWN = timedelta(minutes=5)


# ─────────────────────────────────
# ENSURE USER FIELDS (SAFE)
# ─────────────────────────────────

async def ensure_bazar_user(user_id):
    user = await user_collection.find_one({"id": user_id})

    if not user:
        user = {
            "id": user_id,
            "balance": 0,
            "characters": [],
            "bazar_count": 0,
            "bazar_cooldown": None
        }
        await user_collection.insert_one(user)
        return user

    updates = {}
    if "balance" not in user:
        updates["balance"] = 0
    if "characters" not in user:
        updates["characters"] = []
    if "bazar_count" not in user:
        updates["bazar_count"] = 0
    if "bazar_cooldown" not in user:
        updates["bazar_cooldown"] = None

    if updates:
        await user_collection.update_one(
            {"id": user_id},
            {"$set": updates}
        )
        user.update(updates)

    return user


# ─────────────────────────────────
# /bazar COMMAND
# ─────────────────────────────────

@bot.on_message(filters.command("bazar"))
async def bazar_cmd(_, message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🟢 Common / Low (500)", callback_data="bazar_low")],
            [InlineKeyboardButton("🟠 Medium (1500)", callback_data="bazar_medium")],
            [InlineKeyboardButton("🔴 High (3000)", callback_data="bazar_high")]
        ]
    )

    await message.reply_text(
        "🛒 **Welcome to the Bazar**\n\n"
        "Choose a category to buy a random character:",
        reply_markup=keyboard
    )


# ─────────────────────────────────
# BAZAR CALLBACK
# ─────────────────────────────────

@bot.on_callback_query(filters.regex("^bazar_"))
async def bazar_callback(_, cq: CallbackQuery):
    user_id = cq.from_user.id
    rarity_key = cq.data.split("_")[1]  # low / medium / high
    price = PRICES[rarity_key]

    user = await ensure_bazar_user(user_id)
    now = datetime.utcnow()

    # ⏳ COOLDOWN CHECK
    if user["bazar_cooldown"]:
        if now < user["bazar_cooldown"]:
            remaining = user["bazar_cooldown"] - now
            mins, secs = divmod(int(remaining.total_seconds()), 60)
            return await cq.answer(
                f"⏳ Cooldown active!\nTry again in {mins}m {secs}s",
                show_alert=True
            )
        else:
            # reset cooldown
            await user_collection.update_one(
                {"id": user_id},
                {"$set": {"bazar_count": 0, "bazar_cooldown": None}}
            )
            user["bazar_count"] = 0

    # 💰 BALANCE CHECK
    if user["balance"] < price:
        return await cq.answer(
            f"❌ Not enough coins!\nRequired: {price}\nYou have: {user['balance']}",
            show_alert=True
        )

    # 🎯 FETCH CHARACTER (CORRECT RARITY MATCH)
    rarity_regex = {
        "low": "Low",
        "medium": "Medium",
        "high": "High"
    }[rarity_key]

    character = await collection.aggregate([
        {
            "$match": {
                "rarity": {"$regex": rarity_regex, "$options": "i"},
                "img_url": {"$exists": True, "$ne": ""}
            }
        },
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not character:
        return await cq.answer(
            "❌ No character found in this category.",
            show_alert=True
        )

    char = character[0]

    # 💾 UPDATE USER DATA
    new_count = user["bazar_count"] + 1

    update_data = {
        "$inc": {
            "balance": -price
        },
        "$push": {
            "characters": char
        },
        "$set": {
            "bazar_count": new_count
        }
    }

    # ⏳ START COOLDOWN AFTER 5 PURCHASES
    if new_count >= BAZAR_LIMIT:
        update_data["$set"]["bazar_cooldown"] = now + BAZAR_COOLDOWN
        update_data["$set"]["bazar_count"] = 0

    await user_collection.update_one(
        {"id": user_id},
        update_data
    )

    # 📤 SEND RESULT
    await cq.message.reply_photo(
        photo=char["img_url"],
        caption=(
            "🛒 **Purchase Successful!**\n\n"
            f"👤 Buyer: {cq.from_user.mention}\n"
            f"💃 Name: `{char['name']}`\n"
            f"⭐ Rarity: `{char['rarity']}`\n"
            f"📺 Anime: `{char['anime']}`\n"
            f"💰 Cost: `{price} coins`"
        )
    )

    # ⏳ LIMIT MESSAGE
    if new_count >= BAZAR_LIMIT:
        await cq.message.reply_text(
            "⏳ You bought **5 characters**!\n"
            "Come back after **5 minutes** 🕔"
        )

    await cq.answer("✅ Purchase completed!")
