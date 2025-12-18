import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from TEAMZYRO import ZYRO as bot
from TEAMZYRO import user_collection, collection

# ─── PRICES ─────────────────────────────
PRICES = {
    "common": 500,
    "medium": 1500,
    "high": 3000
}

# ─── RARITY MAPPING (MATCH DB) ──────────
RARITY_MAP = {
    "common": ["Low"],
    "medium": ["Medium"],
    "high": ["High"]
}


# ─── /bazar COMMAND ─────────────────────
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


# ─── CALLBACK HANDLER ───────────────────
@bot.on_callback_query(filters.regex("^bazar_"))
async def bazar_callback(_, cq: CallbackQuery):
    user = cq.from_user
    rarity_key = cq.data.split("_")[1]   # common / medium / high
    price = PRICES[rarity_key]
    valid_rarities = RARITY_MAP[rarity_key]

    # Get user
    user_data = await user_collection.find_one({"id": user.id})
    if not user_data:
        return await cq.answer("❌ You are not registered!", show_alert=True)

    balance = user_data.get("balance", 0)
    if balance < price:
        return await cq.answer(
            f"❌ Not enough balance!\nRequired: {price}\nYou have: {balance}",
            show_alert=True
        )

    # Fetch random character
    character = await collection.aggregate([
        {
            "$match": {
                "rarity": {"$in": valid_rarities},
                "img_url": {"$exists": True, "$ne": ""}
            }
        },
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not character:
        return await cq.answer("❌ No character found in this category.", show_alert=True)

    char = character[0]

    # Update user
    await user_collection.update_one(
        {"id": user.id},
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
            f"👤 Buyer: {user.mention}\n"
            f"💃 Name: `{char['name']}`\n"
            f"⭐ Rarity: `{char['rarity']}`\n"
            f"📺 Anime: `{char['anime']}`\n"
            f"💰 Cost: `{price}` coins"
        )
    )

    await cq.answer("✅ Purchase completed!")
