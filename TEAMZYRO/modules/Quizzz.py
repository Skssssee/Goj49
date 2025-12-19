import random
from pyrogram import filters
from TEAMZYRO import app, character_collection, user_collection, active_guess_collection

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

REWARD_COINS = 50

RARITIES = [
    "Low",
    "Medium",
    "High",
    "Special Edition",
    "Elite Edition",
    "Exclusive",
    "Valentine",
    "Halloween",
    "Winter",
    "Summer",
    "Royal",
    "Luxury Edition"
]

# ─────────────────────────────
# HELPERS
# ─────────────────────────────

async def get_random_character():
    """
    Sab rarities same priority.
    Pehle rarity choose, phir us rarity ka random character.
    """
    for _ in range(10):  # retry safety
        rarity = random.choice(RARITIES)

        chars = await character_collection.find({
            "rarity": rarity,
            "img_url": {"$exists": True, "$ne": ""}
        }).to_list(length=50)

        if chars:
            return random.choice(chars)

    return None


async def start_new_guess(chat_id, message):
    char = await get_random_character()

    if not char:
        await message.reply_text("❌ Character Guess not available.")
        return

    await active_guess_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"character_id": char["id"]}},
        upsert=True
    )

    await message.reply_photo(
        photo=char["img_url"],
        caption=(
            "🎯 **Guess the Character**\n\n"
            f"📺 Anime: **{char['anime']}**\n"
            f"💎 Rarity: **{char['rarity']}**\n\n"
            "✍️ Type character name"
        )
    )

# ─────────────────────────────
# /guess COMMAND
# ─────────────────────────────

@app.on_message(filters.command("guess"))
async def guess_command(_, message):
    chat_id = message.chat.id

    active = await active_guess_collection.find_one({"chat_id": chat_id})
    if active:
        await message.reply_text("❗ Guess already running.")
        return

    await start_new_guess(chat_id, message)

# ─────────────────────────────
# TEXT HANDLER (GUESS CHECK)
# ─────────────────────────────

@app.on_message(filters.text)
async def guess_handler(_, message):
    if message.text.startswith("/"):
        return

    chat_id = message.chat.id
    guess_text = message.text.strip().lower()

    active = await active_guess_collection.find_one({"chat_id": chat_id})
    if not active:
        return

    char = await character_collection.find_one({"id": active["character_id"]})
    if not char:
        return

    correct_name = char["name"].strip().lower()

    # ❌ WRONG GUESS
    if guess_text != correct_name:
        await message.reply_text("❌ Wrong! Try again.")
        return

    # ✅ CORRECT GUESS
    await user_collection.update_one(
        {"id": message.from_user.id},
        {"$inc": {"coins": REWARD_COINS}},
        upsert=True
    )

    await active_guess_collection.delete_one({"chat_id": chat_id})

    await message.reply_text(
        f"✅ **Correct Guess!**\n\n"
        f"🏆 **{char['name']}**\n"
        f"💎 Rarity: {char['rarity']}\n"
        f"💰 +{REWARD_COINS} coins\n\n"
        "➡️ New guess starting..."
    )

    await start_new_guess(chat_id, message)
