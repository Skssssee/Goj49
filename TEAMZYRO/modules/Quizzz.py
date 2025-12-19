import random
from pyrogram import filters
from pyrogram.types import Message
from TEAMZYRO import app, user_collection, collection

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
    rarity = random.choice(RARITIES)

    char = await collection.find_one(
        {
            "rarity": {
                "$regex": f"^{rarity}$",
                "$options": "i"
            },
            "img_url": {"$exists": True}
        }
    )

    return char


async def set_active_guess(user_id, char):
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"active_guess": char}},
        upsert=True
    )


async def clear_active_guess(user_id):
    await user_collection.update_one(
        {"id": user_id},
        {"$unset": {"active_guess": ""}}
    )

# ─────────────────────────────
# /guess COMMAND
# ─────────────────────────────

@app.on_message(filters.command("guess"))
async def guess_cmd(_, message: Message):
    user_id = message.from_user.id

    user = await user_collection.find_one({"id": user_id}) or {}

    # If already guessing → same character
    char = user.get("active_guess")

    if not char:
        char = await get_random_character()

        if not char:
            return await message.reply_text("❌ Character Guess not available.")

        await set_active_guess(user_id, char)

    caption = (
        "❓ **Guess the Character**\n\n"
        f"📺 Anime: `{char['anime']}`\n"
        f"⭐ Rarity: `{char['rarity']}`\n\n"
        "✍️ Type the **character name**"
    )

    await message.reply_photo(
        photo=char["img_url"],
        caption=caption
    )

# ─────────────────────────────
# GUESS HANDLER (TEXT ONLY)
# ─────────────────────────────

@app.on_message(filters.text & ~filters.command())
async def guess_handler(_, message: Message):
    user_id = message.from_user.id
    guess = message.text.strip().lower()

    user = await user_collection.find_one({"id": user_id})
    if not user or "active_guess" not in user:
        return

    char = user["active_guess"]
    correct_name = char["name"].strip().lower()

    # ❌ WRONG GUESS
    if guess != correct_name:
        return await message.reply_text("❌ Wrong guess! Try again.")

    # ✅ CORRECT GUESS
    await clear_active_guess(user_id)

    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"coins": REWARD_COINS},
            "$push": {"characters": char}
        },
        upsert=True
    )

    await message.reply_text(
        f"🎉 **Correct!**\n\n"
        f"👤 {char['name']}\n"
        f"⭐ {char['rarity']}\n\n"
        f"💰 +{REWARD_COINS} coins awarded!"
    )

    # Auto next guess
    next_char = await get_random_character()
    if next_char:
        await set_active_guess(user_id, next_char)

        await message.reply_photo(
            photo=next_char["img_url"],
            caption=(
                "🔁 **New Guess Appeared!**\n\n"
                f"📺 Anime: `{next_char['anime']}`\n"
                f"⭐ Rarity: `{next_char['rarity']}`\n\n"
                "✍️ Guess the name"
            )
        )
