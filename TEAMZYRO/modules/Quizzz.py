import random
from pyrogram import filters
from TEAMZYRO import app, user_collection, collection


# ─────────────────────────────
# CONFIG
# ─────────────────────────────

ALLOWED_RARITIES = ["Low", "Medium", "High"]
REWARD_COINS = 50


# ─────────────────────────────
# START GUESS
# ─────────────────────────────

@app.on_message(filters.command("guess"))
async def start_guess(_, message):
    user_id = message.from_user.id

    # random rarity
    rarity = random.choice(ALLOWED_RARITIES)

    # fetch character from DB
    char = await collection.find_one(
        {
            "rarity": rarity,
            "img_url": {"$exists": True, "$ne": ""}
        }
    )

    if not char:
        return await message.reply_text(
            "❌ character Guess not available."
        )

    # save active guess
    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"active_guess": char}},
        upsert=True
    )

    caption = (
        f"🎯 **Guess the Character**\n\n"
        f"⭐ Rarity: `{char['rarity']}`\n"
        f"🎁 Reward: `+50 Coins`\n\n"
        f"✍️ Type the character name to guess!"
    )

    await message.reply_photo(
        photo=char["img_url"],
        caption=caption
    )


# ─────────────────────────────
# GUESS HANDLER (NO CRASH)
# ─────────────────────────────

@app.on_message(filters.text)
async def guess_handler(_, message):
    # ignore commands
    if message.text.startswith("/"):
        return

    user_id = message.from_user.id
    guess_text = message.text.strip().lower()

    user = await user_collection.find_one({"id": user_id})
    if not user or "active_guess" not in user:
        return

    char = user["active_guess"]
    correct = char["name"].strip().lower()

    # ❌ WRONG GUESS
    if guess_text != correct:
        await message.reply_text("❌ Wrong guess! Try again.")
        return

    # ✅ CORRECT GUESS
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

    # auto start next guess
    await start_guess(_, message)
