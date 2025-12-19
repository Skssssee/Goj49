import random
from pyrogram import filters, enums
from TEAMZYRO import app, collection, user_collection

# ---------------- CONFIG ---------------- #

RARITY_MAP = {
    1: "⚪️ Low",
    2: "🟠 Medium",
    3: "🔴 High",
    4: "🎩 Special Edition",
    5: "🪽 Elite Edition",
    6: "🪐 Exclusive",
    7: "💞 Valentine",
    8: "🎃 Halloween",
    9: "❄️ Winter",
    10: "🏖 Summer",
    11: "🎗 Royal",
    12: "💸 Luxury Edition"
}

REWARD_COINS = 50

# ---------------- UTILS ---------------- #

async def get_random_character_by_rarity():
    """
    Pick random rarity → then random character of that rarity
    """

    rarity_value = random.choice(list(RARITY_MAP.values()))

    chars = await collection.find(
        {
            "rarity": rarity_value,
            "$or": [
                {"img_url": {"$exists": True, "$ne": ""}},
                {"vid_url": {"$exists": True, "$ne": ""}}
            ]
        }
    ).to_list(length=500)

    if not chars:
        return None

    return random.choice(chars)

# ---------------- COMMAND ---------------- #

@app.on_message(filters.command("guess"))
async def guess_cmd(client, message):

    char = await get_random_character_by_rarity()

    if not char:
        await message.reply_text("❌ No characters available.")
        return

    caption = (
        "🎯 **Guess The Character!**\n\n"
        f"⭐ **Rarity:** {char.get('rarity','Unknown')}\n"
        "🧠 Type the character name to guess!\n\n"
        "🎁 Reward: **50 Coins**"
    )

    # Save current guess (important)
    await user_collection.update_one(
        {"id": message.from_user.id},
        {
            "$set": {
                "current_guess": {
                    "id": char["id"],
                    "answer": char["name"]
                }
            }
        },
        upsert=True
    )

    if char.get("vid_url"):
        await message.reply_video(
            char["vid_url"],
            caption=caption,
            parse_mode=enums.ParseMode.MARKDOWN
        )
    else:
        await message.reply_photo(
            char["img_url"],
            caption=caption,
            parse_mode=enums.ParseMode.MARKDOWN
        )
