import random
from pyrogram import filters
from TEAMZYRO import app, user_collection, collection

# ===============================
# CONFIG
# ===============================

REWARD_COINS = 50
RARITIES = ["Low", "Medium", "High"]

# ===============================
# START GUESS COMMAND
# ===============================

@app.on_message(filters.command("guess"))
async def start_guess(_, message):
    user_id = message.from_user.id

    # Pick random character from DB (Low / Medium / High only)
    char = await collection.aggregate([
        {"$match": {
            "rarity": {"$in": RARITIES},
            "img_url": {"$exists": True, "$ne": ""}
        }},
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not char:
        return await message.reply_text("❌ Character Guess not available.")

    char = char[0]

    # Save active guess
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"active_guess": char}},
        upsert=True
    )

    await message.reply_photo(
        photo=char["img_url"],
        caption=(
            "🎯 **Guess the Character!**\n\n"
            f"⭐ Rarity: `{char['rarity']}`\n"
            "✍️ Type the character name to guess\n\n"
            "💰 Reward: **50 Coins**"
        )
    )

# ===============================
# GUESS HANDLER (TEXT ONLY)
# ===============================

@app.on_message(filters.text & ~filters.command)
async def guess_handler(_, message):
    user_id = message.from_user.id
    guess = message.text.strip().lower()

    user = await user_collection.find_one({"id": user_id})
    if not user or "active_guess" not in user:
        return

    char = user["active_guess"]
    correct_name = char["name"].strip().lower()

    # ❌ Wrong guess
    if guess != correct_name:
        await message.reply_text("❌ Wrong guess, try again.")
        return

    # ✅ Correct guess
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"coins": REWARD_COINS},
            "$push": {"characters": char},
            "$unset": {"active_guess": ""}
        }
    )

    await message.reply_text(
        f"✅ **Correct Guess!**\n\n"
        f"👤 {char['name']}\n"
        f"⭐ {char['rarity']}\n"
        f"💰 +{REWARD_COINS} Coins"
    )

    # Auto start next guess
    await start_guess(_, message)
