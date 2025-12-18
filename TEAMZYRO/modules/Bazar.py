
import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection

# Prices
PRICES = {
    "common": 500,
    "medium": 1500,
    "high": 3000
}

# REAL rarity values stored in DB
RARITY_MAP = {
    "common": ["🟢 Low"],
    "medium": ["🟠 Medium"],
    "high": ["🔴 High"]
}

# ─── /bazar ─────────────────────────
@bot.on_message(filters.command("bazar"))
async def bazar_cmd(_, message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🟢 Common (500)", callback_data="bazar_common")],
            [InlineKeyboardButton("🟠 Medium (1500)", callback_data="bazar_medium")],
            [InlineKeyboardButton("🔴 High (3000)", callback_data="bazar_high")]
        ]
    )

    await message.reply_text(
        "🛒 **Welcome to the Bazar!**\n\nChoose a category:",
        reply_markup=keyboard
    )


# ─── BUTTON HANDLER ──────────────────
@bot.on_callback_query(filters.regex("^bazar_"))
async def bazar_callback(_, cq: CallbackQuery):
    user_id = cq.from_user.id
    rarity_key = cq.data.split("_")[1]  # common / medium / high
    price = PRICES[rarity_key]
    rarity_values = RARITY_MAP[rarity_key]

    # Ensure user exists
    user = await user_collection.find_one({"id": user_id})
    if not user:
        return await cq.answer("❌ You are not registered!", show_alert=True)

    balance = user.get("balance", 0)
    if balance < price:
        return await cq.answer(
            f"❌ Not enough coins!\nRequired: {price}\nYou have: {balance}",
            show_alert=True
        )

    # ✅ FETCH CHARACTER CORRECTLY
    chars = await collection.aggregate([
        {
            "$match": {
                "rarity": {"$in": rarity_values},
                "img_url": {"$exists": True, "$ne": ""}
            }
        },
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not chars:
        return await cq.answer(
            "❌ No character found in this category.",
            show_alert=True
        )

    char = chars[0]

    # Deduct balance & give character
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"balance": -price},
            "$push": {"characters": char}
        }
    )

    # Send result
    await cq.message.reply_photo(
        photo=char["img_url"],
        caption=(
            f"🛒 **Purchase Successful!**\n\n"
            f"👤 Buyer: {cq.from_user.mention}\n"
            f"💃 Name: `{char['name']}`\n"
            f"⭐ Rarity: `{char['rarity']}`\n"
            f"📺 Anime: `{char['anime']}`\n"
            f"💰 Cost: `{price} coins`"
        )
    )

    await cq.answer("✅ Purchase completed!")
