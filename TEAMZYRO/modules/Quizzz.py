from pyrogram import filters
from TEAMZYRO import app
from TEAMZYRO import user_collection, collection
from pymongo import ReturnDocument
import random

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

RARITIES = ["Low", "Medium", "High"]
REWARD_COINS = 50

# Active guess stored per chat
active_guess = {}  # {chat_id: character_doc}


# ─────────────────────────────
# START GUESS
# ─────────────────────────────

@app.on_message(filters.command("guess"))
async def start_guess(_, message):
    chat_id = message.chat.id

    # If guess already running
    if chat_id in active_guess:
        return await message.reply_text(
            "🎯 Guess already running!\n"
            "✍️ Type character name to guess."
        )

    rarity = random.choice(RARITIES)

    chars = await collection.find({
        "rarity": rarity,
        "img_url": {"$exists": True, "$ne": ""}
    }).to_list(length=100)

    if not chars:
        return await message.reply_text(
            f"❌ No characters available for rarity: {rarity}"
        )

    char = random.choice(chars)
    active_guess[chat_id] = char

    await message.reply_photo(
        photo=char["img_url"],
        caption=(
            "🎯 **GUESS THE CHARACTER**\n\n"
            f"📺 Anime: **{char['anime']}**\n"
            f"💎 Rarity: **{char['rarity']}**\n\n"
            "✍️ Type the **character name**"
        )
    )


# ─────────────────────────────
# GUESS HANDLER
# ─────────────────────────────

@app.on_message(filters.text)
async def handle_guess(_, message):
    chat_id = message.chat.id

    # Ignore commands
    if message.text.startswith("/"):
        return

    if chat_id not in active_guess:
        return

    char = active_guess[chat_id]
    user_guess = message.text.strip().lower()

    if user_guess != char["name"].lower():
        return await message.reply_text("❌ Wrong guess! Try again.")

    # ✅ Correct Guess
    await user_collection.update_one(
        {"id": message.from_user.id},
        {"$inc": {"coins": REWARD_COINS}},
        upsert=True
    )

    del active_guess[chat_id]

    await message.reply_text(
        f"✅ **Correct Guess!**\n\n"
        f"🏆 Character: **{char['name']}**\n"
        f"💰 Reward: **+{REWARD_COINS} coins**\n\n"
        "➡️ New character incoming..."
    )

    # Start new guess automatically
    await start_guess(_, message)
