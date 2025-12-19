import random
from pyrogram import filters
from TEAMZYRO import app, collection, user_collection

# ─────────────────────────────
# CONFIG
# ─────────────────────────────

GUESS_REWARD = 50

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

# rarity weight (chance)
RARITY_WEIGHT = {
    "Low": 30,
    "Medium": 25,
    "High": 15,
    "Special Edition": 8,
    "Elite Edition": 6,
    "Exclusive": 5,
    "Valentine": 3,
    "Halloween": 3,
    "Winter": 2,
    "Summer": 2,
    "Royal": 1,
    "Luxury Edition": 0.5
}


# ─────────────────────────────
# PICK RANDOM CHARACTER
# ─────────────────────────────

async def get_random_character():
    rarity = random.choices(
        list(RARITY_WEIGHT.keys()),
        weights=RARITY_WEIGHT.values(),
        k=1
    )[0]

    chars = await collection.find(
        {"rarity": rarity, "img_url": {"$exists": True}}
    ).to_list(length=100)

    if not chars:
        return None

    return random.choice(chars)


# ─────────────────────────────
# /guess COMMAND
# ─────────────────────────────

@app.on_message(filters.command("guess"))
async def guess_cmd(_, message):
    user_id = message.from_user.id

    user = await user_collection.find_one({"id": user_id}) or {}

    # If already guessing, show same character
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

    caption = (
        "❓ **GUESS THE CHARACTER**\n\n"
        f"🎴 **Rarity:** `{char['rarity']}`\n"
        "✍️ Reply with the character name"
    )

    await message.reply_photo(
        photo=char["img_url"],
        caption=caption
    )


# ─────────────────────────────
# GUESS ANSWER HANDLER
# ─────────────────────────────

@app.on_message(filters.text & ~filters.command)
async def guess_answer(_, message):
    user_id = message.from_user.id
    guess = message.text.strip().lower()

    user = await user_collection.find_one({"id": user_id})
    if not user or not user.get("active_guess"):
        return

    char = user["active_guess"]
    correct = char["name"].strip().lower()

    # ❌ WRONG GUESS
    if guess != correct:
        return await message.reply_text("❌ Wrong guess! Try again.")

    # ✅ CORRECT GUESS
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"coins": GUESS_REWARD},
            "$unset": {"active_guess": ""}
        }
    )

    await message.reply_text(
        f"🎉 **Correct!**\n\n"
        f"🧩 `{char['name']}` guessed successfully!\n"
        f"💰 +{GUESS_REWARD} coins earned"
    )

    # Auto show next character
    await guess_cmd(_, message)
