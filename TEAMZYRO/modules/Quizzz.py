from pyrogram import filters
from TEAMZYRO import app, character_collection, user_collection, active_guess_collection
import random

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

RARITIES = ["Low", "Medium", "High"]
REWARD = 50


# ─────────────────────────────
# START GUESS
# ─────────────────────────────

@app.on_message(filters.command("guess"))
async def start_guess(_, message):
    chat_id = message.chat.id

    # Check if guess already running
    if await active_guess_collection.find_one({"chat_id": chat_id}):
        await message.reply_text("❗ Guess already running in this chat.")
        return

    rarity = random.choice(RARITIES)

    chars = await character_collection.find(
        {
            "rarity": rarity,
            "img_url": {"$exists": True, "$ne": ""}
        }
    ).to_list(length=50)

    if not chars:
        await message.reply_text("❌ No characters found.")
        return

    char = random.choice(chars)

    await active_guess_collection.insert_one({
        "chat_id": chat_id,
        "character_id": char["id"]
    })

    await message.reply_photo(
        photo=char["img_url"],
        caption=(
            "🎯 **Guess the Character**\n\n"
            f"📺 Anime: `{char['anime']}`\n"
            f"💎 Rarity: `{char['rarity']}`\n"
            f"💰 Reward: `+{REWARD} Coins`\n\n"
            "✍️ Type the character name"
        )
    )


# ─────────────────────────────
# GUESS HANDLER
# ─────────────────────────────

@app.on_message(filters.text & ~filters.regex(r"^/"))
async def guess_handler(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    guess = message.text.strip().lower()

    active = await active_guess_collection.find_one({"chat_id": chat_id})
    if not active:
        return

    char = await character_collection.find_one({"id": active["character_id"]})
    if not char:
        await active_guess_collection.delete_one({"chat_id": chat_id})
        return

    # ❌ Wrong guess
    if guess != char["name"].lower():
        await message.reply_text("❌ Wrong guess! Try again.")
        return

    # ✅ Correct guess
    await user_collection.update_one(
        {"id": user_id},
        {"$inc": {"coins": REWARD}},
        upsert=True
    )

    await active_guess_collection.delete_one({"chat_id": chat_id})

    await message.reply_text(
        f"✅ **Correct Guess!**\n\n"
        f"👤 {char['name']}\n"
        f"💎 {char['rarity']}\n"
        f"💰 +{REWARD} coins\n\n"
        "➡️ New guess starting..."
    )

    # Auto start new guess
    await start_guess(_, message)
