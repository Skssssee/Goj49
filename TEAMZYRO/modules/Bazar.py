import random
from datetime import datetime
from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection


PRICES = {
    "common": 500,
    "medium": 1500,
    "high": 3000
}


# ─── /bazar command ───────────────────────────────────────
@bot.on_message(filters.command("bazar"))
async def bazar_cmd(_, message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🟢 Common (500)", callback_data="bazar_common")],
            [InlineKeyboardButton("🔵 Medium (1500)", callback_data="bazar_medium")],
            [InlineKeyboardButton("🔴 High (3000)", callback_data="bazar_high")]
        ]
    )

    await message.reply_text(
        "🛒 **Welcome to the Bazar!**\n\n"
        "Choose a character category to buy:",
        reply_markup=keyboard
    )


# ─── Button handler ───────────────────────────────────────
@bot.on_callback_query(filters.regex("^bazar_"))
async def bazar_callback(_, cq: CallbackQuery):
    user = cq.from_user
    user_id = user.id
    rarity = cq.data.split("_")[1]  # common / medium / high
    price = PRICES[rarity]

    # Get user
    user_data = await user_collection.find_one({"id": user_id})
    if not user_data:
        return await cq.answer("❌ You are not registered!", show_alert=True)

    coins = user_data.get("coins", 0)
    if coins < price:
        return await cq.answer(
            f"❌ Not enough coins!\nRequired: {price}\nYou have: {coins}",
            show_alert=True
        )

    # Fetch character from DB
    character = await collection.aggregate([
        {
            "$match": {
                "rarity": {"$regex": f"^{rarity}$", "$options": "i"},
                "img_url": {"$exists": True, "$ne": ""}
            }
        },
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not character:
        return await cq.answer("❌ No character found in this category.", show_alert=True)

    char = character[0]

    # Update user (deduct coins + give character)
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"coins": -price},
            "$push": {"characters": char}
        }
    )

    # Send result
    await cq.message.reply_photo(
        photo=char["img_url"],
        caption=(
            f"🛒 **Purchase Successful!**\n\n"
            f"👤 **Buyer:** {user.mention}\n"
            f"💃 **Name:** `{char['name']}`\n"
            f"⭐ **Rarity:** `{char['rarity']}`\n"
            f"📺 **Anime:** `{char['anime']}`\n"
            f"💰 **Cost:** `{price} coins`"
        )
    )

    await cq.answer("✅ Purchase completed!")
