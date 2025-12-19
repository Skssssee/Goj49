from pyrogram import filters
from TEAMZYRO import app, character_collection, user_collection, active_guess_collection
import random

RARITIES = [
    "Low", "Medium", "High", "Special Edition",
    "Elite Edition", "Exclusive", "Valentine",
    "Halloween", "Winter", "Summer", "Royal",
    "Luxury Edition"
]

REWARD_COINS = 50


# 🎯 Start Guess
@app.on_message(filters.command("guess"))
async def start_guess(_, message):
    chat_id = message.chat.id

    active = await active_guess_collection.find_one({"chat_id": chat_id})
    if active:
        await message.reply_text("❗ Guess already running. Type character name to guess.")
        return

    rarity = random.choice(RARITIES)
    chars = await character_collection.find({"rarity": rarity}).to_list(length=100)

    if not chars:
        await message.reply_text("❌ No characters available.")
        return

    char = random.choice(chars)

    await active_guess_collection.insert_one({
        "chat_id": chat_id,
        "character_id": char["id"]
    })

    caption = (
        f"🎯 **Guess the Character!**\n\n"
        f"📺 Anime: {char['anime']}\n"
        f"💎 Rarity: {char['rarity']}\n\n"
        f"✍️ Type character name"
    )

    await message.reply_photo(char["img_url"], caption=caption)


# 🧠 Handle Guess
@app.on_message(filters.text & ~filters.command)
async def handle_guess(_, message):
    chat_id = message.chat.id
    text = message.text.strip().lower()

    active = await active_guess_collection.find_one({"chat_id": chat_id})
    if not active:
        return

    char = await character_collection.find_one({"id": active["character_id"]})
    if not char:
        return

    if text == char["name"].lower():
        user = await user_collection.find_one({"id": message.from_user.id})
        if not user:
            await user_collection.insert_one({
                "id": message.from_user.id,
                "coins": REWARD_COINS
            })
        else:
            await user_collection.update_one(
                {"id": message.from_user.id},
                {"$inc": {"coins": REWARD_COINS}}
            )

        await active_guess_collection.delete_one({"chat_id": chat_id})

        await message.reply_text(
            f"✅ **Correct!** 🎉\n"
            f"🏆 {char['name']}\n"
            f"💰 +{REWARD_COINS} coins\n\n"
            f"➡️ New guess starting..."
        )

        # Auto start next guess
        await start_guess(_, message)

    else:
        await message.reply_text("❌ Wrong guess! Try again 😈")
