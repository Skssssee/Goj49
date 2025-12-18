from datetime import datetime, timedelta
from pyrogram import filters
from TEAMZYRO import ZYRO as bot, user_collection

# ─── CONFIG ─────────────────────────────────────────
HOURLY_COINS = 100
DAILY_COINS = 500

HOURLY_CD = timedelta(hours=1)
DAILY_CD = timedelta(hours=24)

# 🔒 PERMANENT ADMIN
ADMIN_IDS = [1334658171]


# ─── GET OR CREATE USER (AUTO-FIX OLD USERS) ─────────
async def get_user(user):
    data = await user_collection.find_one({"id": user.id})

    if not data:
        data = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "coins": 0,
            "tokens": 0,
            "last_hourly": None,
            "last_daily": None,
            "daily_streak": 0,
            "vip": False,
            "characters": []
        }
        await user_collection.insert_one(data)
        return data

    updates = {}

    if "coins" not in data:
        updates["coins"] = 0
    if "tokens" not in data:
        updates["tokens"] = 0
    if "last_hourly" not in data:
        updates["last_hourly"] = None
    if "last_daily" not in data:
        updates["last_daily"] = None
    if "daily_streak" not in data:
        updates["daily_streak"] = 0
    if "vip" not in data:
        updates["vip"] = False
    if "characters" not in data:
        updates["characters"] = []

    if updates:
        await user_collection.update_one(
            {"id": user.id},
            {"$set": updates}
        )
        data.update(updates)

    return data


# ─── BALANCE ─────────────────────────────────────────
@bot.on_message(filters.command("balance"))
async def balance_cmd(_, message):
    user = await get_user(message.from_user)

    await message.reply_text(
        f"💳 **Your Wallet**\n\n"
        f"🪙 Coins: `{user['coins']}`\n"
        f"🎟 Tokens: `{user.get('tokens', 0)}`\n"
        f"🔥 Daily Streak: `{user['daily_streak']}`\n"
        f"💎 VIP: `{user['vip']}`"
    )


# ─── HOURLY ──────────────────────────────────────────
@bot.on_message(filters.command("hourly"))
async def hourly_cmd(_, message):
    user = await get_user(message.from_user)
    now = datetime.utcnow()

    if user["last_hourly"]:
        remaining = HOURLY_CD - (now - user["last_hourly"])
        if remaining.total_seconds() > 0:
            m, s = divmod(int(remaining.total_seconds()), 60)
            return await message.reply_text(
                f"⏳ Try again in `{m}m {s}s`"
            )

    reward = HOURLY_COINS * (2 if user["vip"] else 1)

    await user_collection.update_one(
        {"id": user["id"]},
        {
            "$inc": {"coins": reward},
            "$set": {"last_hourly": now}
        }
    )

    await message.reply_text(
        f"🪙 You received **{reward} coins** (Hourly)"
    )


# ─── DAILY ───────────────────────────────────────────
@bot.on_message(filters.command("daily"))
async def daily_cmd(_, message):
    user = await get_user(message.from_user)
    now = datetime.utcnow()

    if user["last_daily"]:
        diff = now - user["last_daily"]
        if diff < DAILY_CD:
            h = int((DAILY_CD - diff).total_seconds() // 3600)
            return await message.reply_text(
                f"⏳ Come back in `{h}h`"
            )

        streak = user["daily_streak"] + 1 if diff <= timedelta(hours=48) else 1
    else:
        streak = 1

    bonus = min(streak * 50, 500)
    reward = DAILY_COINS + bonus
    if user["vip"]:
        reward *= 2

    await user_collection.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "last_daily": now,
                "daily_streak": streak
            },
            "$inc": {"coins": reward}
        }
    )

    await message.reply_text(
        f"🌞 **Daily Reward Claimed!**\n\n"
        f"🪙 Coins: `{reward}`\n"
        f"🔥 Streak: `{streak}`"
    )


# ─── PAY USER ───────────────────────────────────────
@bot.on_message(filters.command("pay"))
async def pay_cmd(_, message):
    sender = await get_user(message.from_user)

    if not message.reply_to_message:
        return await message.reply_text("Reply to a user to pay coins.")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /pay amount")

    try:
        amount = int(message.command[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await message.reply_text("Invalid amount.")

    if sender["coins"] < amount:
        return await message.reply_text("❌ Not enough coins.")

    receiver = await get_user(message.reply_to_message.from_user)

    await user_collection.update_one(
        {"id": sender["id"], "coins": {"$gte": amount}},
        {"$inc": {"coins": -amount}}
    )
    await user_collection.update_one(
        {"id": receiver["id"]},
        {"$inc": {"coins": amount}}
    )

    await message.reply_text(
        f"✅ Paid `{amount}` coins to {receiver['first_name']}"
    )


# ─── ADMIN ADD COINS ─────────────────────────────────
@bot.on_message(filters.command("addcoins") & filters.user(ADMIN_IDS))
async def addcoins_cmd(_, message):
    if len(message.command) < 3:
        return await message.reply_text("/addcoins user_id amount")

    uid = int(message.command[1])
    amt = int(message.command[2])

    await user_collection.update_one(
        {"id": uid},
        {"$inc": {"coins": amt}},
        upsert=True
    )

    await message.reply_text(f"✅ Added `{amt}` coins to `{uid}`")


# ─── ADMIN REMOVE COINS ──────────────────────────────
@bot.on_message(filters.command("removecoins") & filters.user(ADMIN_IDS))
async def removecoins_cmd(_, message):
    if len(message.command) < 3:
        return await message.reply_text("/removecoins user_id amount")

    uid = int(message.command[1])
    amt = int(message.command[2])

    await user_collection.update_one(
        {"id": uid},
        {"$inc": {"coins": -amt}}
    )

    await message.reply_text(f"❌ Removed `{amt}` coins from `{uid}`")
