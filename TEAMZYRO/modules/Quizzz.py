
import random
from html import escape
from pyrogram import filters
from pyrogram.enums import ParseMode
from TEAMZYRO import app, collection, user_collection

# ───────── CONFIG ─────────

REWARD_COINS = 50

RARITY_MAP = {
    "⚪️ Low",
    "🟠 Medium",
    "🔴 High",
    "🎩 Special Edition",
    "🪽 Elite Edition",
    "🪐 Exclusive",
    "💞 Valentine",
    "🎃 Halloween",
    "❄️ Winter",
    "🏖 Summer",
    "🎗 Royal",
    "💸 Luxury Edition"
}

# ───────── HELPERS ─────────

async def get_random_character():
    chars = await collection.find(
        {
            "rarity": {"$in": list(RARITY_MAP)},
            "img_url": {"$exists": True, "$ne": ""}
        }
    ).to_list(length=500)

    if not chars:
        return None

    return random.choice(chars)


# ───────── /guess COMMAND ─────────

@app.on_message(filters.command("guess"))
async def guess_cmd(_, message):
    user_id = message.from_user.id

    char = await get_random_character()
    if not char:
        return await message.reply_text("❌ No characters available.")

    # Save active guess
    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {
                "active_guess": {
                    "id": char["id"],
                    "name": char["name"].lower()
                }
            }
        },
        upsert=True
    )

    rarity = char.get("rarity", "Unknown")

    caption = (
        "🎯 <b>GUESS THE CHARACTER!</b>\n\n"
        f"💎 <b>Rarity:</b> <code>{escape(rarity)}</code>\n\n"
        "✍️ Type your answer:\n"
        "<code>/answer character_name</code>"
    )

    await message.reply_photo(
        photo=char["img_url"],
        caption=caption,
        parse_mode=ParseMode.HTML
    )


# ───────── /answer COMMAND ─────────

@app.on_message(filters.command("answer"))
async def answer_cmd(_, message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        return await message.reply_text("❌ Usage: /answer <character name>")

    answer = args[1].lower().strip()

    user = await user_collection.find_one({"id": user_id})
    if not user or "active_guess" not in user:
        return await message.reply_text("❌ No active guess. Use /guess first.")

    active = user["active_guess"]

    if answer != active["name"]:
        return await message.reply_text("❌ Wrong answer. Try again!")

    # Fetch character
    char = await collection.find_one({"id": active["id"]})
    if not char:
        return await message.reply_text("❌ Character data missing.")

    # Add coins
    coins = user.get("coins", 0) + REWARD_COINS

    # Update user
    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {
                "coins": coins,
                "active_guess": None
            },
            "$push": {
                "characters": char
            }
        }
    )

    rarity = char.get("rarity", "Unknown")

    success_text = (
        "✨ <b>CORRECT GUESS!</b> ✨\n\n"
        f"👤 <b>{escape(char['name'])}</b>\n"
        f"📺 <b>Anime:</b> {escape(char.get('anime','Unknown'))}\n"
        f"💎 <b>Rarity:</b> <code>{escape(rarity)}</code>\n\n"
        f"💰 <b>+{REWARD_COINS} coins earned!</b>\n"
        f"🏦 <b>Total Coins:</b> <code>{coins}</code>\n\n"
        "➡️ Use /guess for next character!"
    )

    await message.reply_text(
        success_text,
        parse_mode=ParseMode.HTML
    )
