import random
from pyrogram import filters
from TEAMZYRO import app, collection, user_collection

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
# PICK RANDOM CHARACTER BY RARITY
# ─────────────────────────────

async def get_random_character():
    rarity = random.choice(RARITIES)

    chars = await collection.aggregate([
        {"$match": {
            "rarity": rarity,
            "img_url": {"$exists": True, "$ne": ""}
        }},
        {"$sample": {"size": 1}}
    ]).to_list(1)

    if not chars:
        return None

    return chars[0]

# ─────────────────────────────
# /guess COMMAND
# ─────────────────────────────

@app.on_message(filters.command("guess"))
async def guess_cmd(_, message):
    user_id = message.from_user.id

    user = await user_collection.find_one({"id": user_id}) or {
        "id": user_id,
        "coins": 0
    }

    # Agar already active guess hai → wahi dikhana
    if user.get("active_guess"):
        char = user["active_guess"]
    else:
        char = await get_random_character()
        if not char:
            return await message.reply_text("❌ No characters available.")

        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"active_guess": char}},
            upsert=True
        )

    await message.reply_photo(
        photo=char["img_url"],
        caption=(
            "🎯 **GUESS THE CHARACTER**\n\n"
            f"⭐ Rarity: **{char['rarity']}**\n"
            "✍️ Type the character name"
        )
    )

# ─────────────────────────────
# TEXT ANSWER HANDLER
# ─────────────────────────────

@app.on_message(filters.text & ~filters.command())
async def handle_guess(_, message):
    user_id = message.from_user.id
    answer = message.text.strip().lower()

    user = await user_collection.find_one({"id": user_id})
    if not user or not user.get("active_guess"):
        return

    char = user["active_guess"]
    correct_name = char["name"].strip().lower()

    # ❌ WRONG GUESS
    if answer != correct_name:
        return await message.reply_text("❌ Wrong guess! Try again.")

    # ✅ CORRECT GUESS
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"coins": REWARD_COINS},
            "$unset": {"active_guess": ""}
        }
    )

    await message.reply_text(
        f"🎉 **Correct!**\n\n"
        f"🧩 `{char['name']}`\n"
        f"💰 +{REWARD_COINS} coins"
    )

    # Auto next guess
    next_char = await get_random_character()
    if not next_char:
        return

    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"active_guess": next_char}}
    )

    await message.reply_photo(
        photo=next_char["img_url"],
        caption=(
            "🎯 **NEXT GUESS**\n\n"
            f"⭐ Rarity: **{next_char['rarity']}**\n"
            "✍️ Guess the character name"
        )
    )
