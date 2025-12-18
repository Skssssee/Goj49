import random
import time
from pyrogram import filters
from pyrogram.types import Message

from TEAMZYRO import app, user_collection

# ─── CONFIG ────────────────────────────────────────
WIN_RATE = 0.40        # 40% winning probability
SLOT_CD = 30           # seconds
DICE_CD = 30

MIN_BET = 10
MAX_BET = 500

SLOT_EMOJIS = ["🍒", "🍋", "🍉", "🍇", "💎"]

# cooldown memory (very light)
slot_cd = {}
dice_cd = {}

# ─── ENSURE USER ───────────────────────────────────
async def ensure_user(user):
    data = await user_collection.find_one({"id": user.id})
    if not data:
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "balance": 0,
            "tokens": 0,
            "characters": []
        }
        await user_collection.insert_one(data)
    if "balance" not in data:
        await user_collection.update_one(
            {"id": user.id},
            {"$set": {"balance": 0}}
        )
        data["balance"] = 0
    return data


# ─── SLOT GAME ─────────────────────────────────────
@app.on_message(filters.command("slot"))
async def slot_game(_, message: Message):
    uid = message.from_user.id
    args = message.text.split()

    if len(args) != 2 or not args[1].isdigit():
        return await message.reply_text("❌ Usage: /slot <bet>")

    bet = int(args[1])
    if bet < MIN_BET or bet > MAX_BET:
        return await message.reply_text("❌ Invalid bet amount.")

    now = time.time()
    if uid in slot_cd and now - slot_cd[uid] < SLOT_CD:
        return await message.reply_text(
            f"⏳ Cooldown: {int(SLOT_CD - (now - slot_cd[uid]))}s"
        )

    user = await ensure_user(message.from_user)
    if user["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance.")

    slot_cd[uid] = now
    spin = [random.choice(SLOT_EMOJIS) for _ in range(3)]
    win = random.random() <= WIN_RATE

    text = "🎰 SLOT MACHINE 🎰\n\n" + " | ".join(spin) + "\n\n"

    if win:
        reward = bet
        await user_collection.update_one(
            {"id": uid},
            {"$inc": {"balance": reward}}
        )
        text += f"🎉 YOU WON +{reward} coins!"
    else:
        await user_collection.update_one(
            {"id": uid},
            {"$inc": {"balance": -bet}}
        )
        text += f"💀 YOU LOST -{bet} coins!"

    bal = (await user_collection.find_one({"id": uid}))["balance"]
    text += f"\n\n💰 Balance: {bal}"

    await message.reply_text(text)


# ─── DICE GAME ─────────────────────────────────────
@app.on_message(filters.command("dice"))
async def dice_game(_, message: Message):
    uid = message.from_user.id
    args = message.text.split()

    if len(args) != 2 or not args[1].isdigit():
        return await message.reply_text("❌ Usage: /dice <bet>")

    bet = int(args[1])
    if bet < MIN_BET or bet > MAX_BET:
        return await message.reply_text("❌ Invalid bet amount.")

    now = time.time()
    if uid in dice_cd and now - dice_cd[uid] < DICE_CD:
        return await message.reply_text(
            f"⏳ Cooldown: {int(DICE_CD - (now - dice_cd[uid]))}s"
        )

    user = await ensure_user(message.from_user)
    if user["balance"] < bet:
        return await message.reply_text("❌ Insufficient balance.")

    dice_cd[uid] = now
    roll = random.randint(1, 6)
    win = random.random() <= WIN_RATE

    if win:
        await user_collection.update_one(
            {"id": uid},
            {"$inc": {"balance": bet}}
        )
        result = f"🎲 Rolled {roll} → 🎉 YOU WON +{bet}"
    else:
        await user_collection.update_one(
            {"id": uid},
            {"$inc": {"balance": -bet}}
        )
        result = f"🎲 Rolled {roll} → 💀 YOU LOST -{bet}"

    bal = (await user_collection.find_one({"id": uid}))["balance"]
    await message.reply_text(f"{result}\n💰 Balance: {bal}")


# ─── DUEL GAME ─────────────────────────────────────
@app.on_message(filters.command("duel"))
async def duel_game(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a user to duel.")

    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return await message.reply_text("❌ Usage: /duel <bet>")

    bet = int(args[1])
    if bet < MIN_BET or bet > MAX_BET:
        return await message.reply_text("❌ Invalid bet amount.")

    u1 = message.from_user
    u2 = message.reply_to_message.from_user

    d1 = await ensure_user(u1)
    d2 = await ensure_user(u2)

    if d1["balance"] < bet or d2["balance"] < bet:
        return await message.reply_text("❌ One player has insufficient balance.")

    winner = u1 if random.random() <= WIN_RATE else u2
    loser = u2 if winner.id == u1.id else u1

    await user_collection.update_one(
        {"id": winner.id},
        {"$inc": {"balance": bet}}
    )
    await user_collection.update_one(
        {"id": loser.id},
        {"$inc": {"balance": -bet}}
    )

    await message.reply_text(
        f"⚔️ DUEL RESULT\n\n"
        f"🏆 Winner: {winner.mention}\n"
        f"💀 Loser: {loser.mention}\n"
        f"💰 Bet: {bet}"
    )


# ─── GAME LEADERBOARD ──────────────────────────────
@app.on_message(filters.command("gameleaderboard"))
async def game_leaderboard(_, message: Message):
    users = await user_collection.find().sort("balance", -1).limit(10).to_list(10)

    text = "🏆 GAME LEADERBOARD 🏆\n\n"
    for i, u in enumerate(users, 1):
        name = u.get("first_name", "Unknown")
        bal = u.get("balance", 0)
        text += f"{i}. {name} → 💰 {bal}\n"

    await message.reply_text(text)
