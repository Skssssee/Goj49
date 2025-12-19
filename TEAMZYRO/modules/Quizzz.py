import random
from pyrogram import filters
from TEAMZYRO import app, collection, user_collection

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


async def get_random_character():
    rarity = random.choice(RARITIES)

    chars = await collection.aggregate([
        {"$match": {"rarity": rarity}},
        {"$sample": {"size": 1}}
    ]).to_list(1)

    return chars[0] if chars else None


# ───────────── /guess ─────────────

@app.on_message(filters.command("guess"))
async def guess_cmd(_, message):
    user_id = message.from_user.id

    user = await user_collection.find_one({"id": user_id}) or {"id": user_id, "coins": 0}

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
        caption=f"🎯 Guess this character\n⭐ Rarity: {char['rarity']}"
    )


# ───────────── ANSWER HANDLER ─────────────
# ⚠️ NO ~filters.command HERE

@app.on_message(filters.text)
async def answer_handler(_, message):
    if message.text.startswith("/"):
        return  # ignore commands safely

    user_id = message.from_user.id
    answer = message.text.strip().lower()

    user = await user_collection.find_one({"id": user_id})
    if not user or not user.get("active_guess"):
        return

    char = user["active_guess"]

    if answer != char["name"].lower():
        return await message.reply_text("❌ Wrong guess, try again.")

    # ✅ Correct
    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"coins": REWARD_COINS},
            "$unset": {"active_guess": ""}
        }
    )

    await message.reply_text(
        f"🎉 Correct!\n"
        f"🧩 {char['name']}\n"
        f"💰 +{REWARD_COINS} coins"
    )

    # Next character
    next_char = await get_random_character()
    if not next_char:
        return

    await user_collection.update_one(
        {"id": user_id},
        {"$set": {"active_guess": next_char}}
    )

    await message.reply_photo(
        photo=next_char["img_url"],
        caption=f"🎯 Next Guess\n⭐ Rarity: {next_char['rarity']}"
    )
