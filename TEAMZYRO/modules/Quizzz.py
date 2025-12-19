from pyrogram import filters
from TEAMZYRO import app, character_collection, user_collection, active_guess_collection
import random

# ───────── CONFIG ─────────
RARITIES = ["Low", "Medium", "High"]
REWARD_COINS = 50


# ───────── START GUESS ─────────
@app.on_message(filters.command("guess"))
async def start_guess(_, message):
    chat_id = message.chat.id

    # Already running?
    active = await active_guess_collection.find_one({"chat_id": chat_id})
    if active:
        await message.reply_text("❗ Guess already running. Guess the character name!")
        return

    # Pick rarity
    rarity = random.choice(RARITIES)

    # Fetch characters of that rarity
    chars = await character_collection.find(
        {"rarity": rarity, "img_url": {"$exists": True, "$ne": ""}}
    ).to_list(length=100)

    if not chars:
        await message.reply_text("❌ No characters available.")
        return

    char = random.choice(chars)

    # Save active guess
    await active_guess_collection.insert_one({
        "chat_id": chat_id,
        "character_id": char["id"]
    })

    await message.reply_photo(
        photo=char["img_url"],
        caption=(
            "🎯 **GUESS THE CHARACTER**\n\n"
            f"📺 Anime: `{char['anime']}`\n"
            f"💎 Rarity: `{char['rarity']}`\n\n"
            "✍️ Type the **character name** in chat"
        )
    )


# ───────── HANDLE ANSWERS ─────────
@app.on_message(filters.text & ~filters.regex(r"^/"))
async def handle_guess(_, message):
    chat_id = message.chat.id
    user_guess = message.text.strip().lower()

    active = await active_guess_collection.find_one({"chat_id": chat_id})
    if not active:
        return  # no guess running

    char = await character_collection.find_one({"id": active["character_id"]})
    if not char:
        await active_guess_collection.delete_one({"chat_id": chat_id})
        return

    correct_name = char["name"].strip().lower()

    # ❌ WRONG
    if user_guess != correct_name:
        await message.reply_text("❌ Wrong guess! Try again.")
        return

    # ✅ CORRECT
    await user_collection.update_one(
        {"id": message.from_user.id},
        {"$inc": {"coins": REWARD_COINS}},
        upsert=True
    )

    await active_guess_collection.delete_one({"chat_id": chat_id})

    await message.reply_text(
        f"✅ **Correct Guess!**\n\n"
        f"👤 **{char['name']}**\n"
        f"💰 +{REWARD_COINS} coins\n\n"
        "🎯 New guess starting..."
    )

    # Start new round
    await start_guess(_, message)
