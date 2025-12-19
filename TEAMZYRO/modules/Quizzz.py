import random
from pyrogram import filters
from TEAMZYRO import app, user_collection, collection


REWARD_COINS = 50


# ─────────────────────────────
# HELPER: RANDOM CHARACTER
# ─────────────────────────────
async def get_random_character():
    chars = await collection.find(
        {
            "$or": [
                {"img_url": {"$exists": True, "$ne": ""}},
                {"vid_url": {"$exists": True, "$ne": ""}}
            ]
        }
    ).to_list(length=500)

    if not chars:
        return None

    return random.choice(chars)


# ─────────────────────────────
# /guess COMMAND
# ─────────────────────────────
@app.on_message(filters.command("guess"))
async def guess_cmd(client, message):
    user_id = message.from_user.id

    user = await user_collection.find_one({"id": user_id}) or {}

    # अगर पहले से guess pending है
    if user.get("current_guess"):
        await message.reply_text(
            "⚠️ **You already have a pending guess!**\n"
            "❓ Guess the current character first."
        )
        return

    char = await get_random_character()

    if not char:
        await message.reply_text("❌ No characters available.")
        return

    rarity = char.get("rarity", "Unknown")

    caption = (
        "🎯 **Guess The Character!**\n\n"
        f"⭐ **Rarity:** {rarity}\n"
        "🧠 Send the character name to guess\n\n"
        f"🎁 Reward: **{REWARD_COINS} Coins**"
    )

    # save current guess
    await user_collection.update_one(
        {"id": user_id},
        {
            "$set": {
                "current_guess": {
                    "id": char["id"],
                    "answer": char["name"].lower()
                }
            }
        },
        upsert=True
    )

    if char.get("vid_url"):
        await message.reply_video(char["vid_url"], caption=caption)
    else:
        await message.reply_photo(char["img_url"], caption=caption)


# ─────────────────────────────
# ANSWER HANDLER
# ─────────────────────────────
@app.on_message(filters.text & ~filters.command)
async def answer_guess(client, message):
    user_id = message.from_user.id
    text = message.text.lower().strip()

    user = await user_collection.find_one({"id": user_id})
    if not user or not user.get("current_guess"):
        return

    correct_answer = user["current_guess"]["answer"]

    # ❌ WRONG ANSWER
    if text != correct_answer:
        await message.reply_text("❌ Wrong guess! Try again.")
        return

    # ✅ CORRECT ANSWER
    new_balance = user.get("balance", 0) + REWARD_COINS

    await user_collection.update_one(
        {"id": user_id},
        {
            "$unset": {"current_guess": ""},
            "$set": {"balance": new_balance}
        }
    )

    await message.reply_text(
        "🎉 **Correct Guess!**\n\n"
        f"💰 You earned **{REWARD_COINS} coins**\n"
        f"🏦 New Balance: `{new_balance}`\n\n"
        "➡️ Use /guess for next character!"
    )
