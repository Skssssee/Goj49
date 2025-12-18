
import time
import html
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from TEAMZYRO import app, user_collection

# ─────────────────────────────────
# CONFIG
# ─────────────────────────────────
BALANCE_GIVER_ID = 1334658171  # ONLY this user can add balance

HOURLY_AMOUNT = 50
DAILY_AMOUNT = 200

HOURLY_COOLDOWN = 3600       # 1 hour
DAILY_COOLDOWN = 86400      # 24 hours


# ─────────────────────────────────
# ENSURE USER (AUTO FIX OLD USERS)
# ─────────────────────────────────
async def ensure_user(user):
    data = await user_collection.find_one({"id": user.id})

    if not data:
        data = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": 0,
            "tokens": 0,
            "characters": [],
            "last_hourly": 0,
            "last_daily": 0
        }
        await user_collection.insert_one(data)
        return data

    updates = {}
    for key, default in {
        "balance": 0,
        "tokens": 0,
        "characters": [],
        "last_hourly": 0,
        "last_daily": 0
    }.items():
        if key not in data:
            updates[key] = default

    if data.get("first_name") != user.first_name:
        updates["first_name"] = user.first_name
    if data.get("username") != user.username:
        updates["username"] = user.username

    if updates:
        await user_collection.update_one(
            {"id": user.id},
            {"$set": updates}
        )
        data.update(updates)

    return data


# ─────────────────────────────────
# BALANCE
# ─────────────────────────────────
@app.on_message(filters.command("balance"))
async def balance_cmd(_, message: Message):
    user = await ensure_user(message.from_user)

    await message.reply_text(
        f"💰 <b>{html.escape(message.from_user.first_name)}'s Balance</b>\n\n"
        f"🪙 Coins: <b>{user['balance']}</b>\n"
        f"🎟 Tokens: <b>{user['tokens']}</b>",
        parse_mode=ParseMode.HTML
    )


# ─────────────────────────────────
# ADD BALANCE (SPECIFIC USER ONLY)
# ─────────────────────────────────
@app.on_message(filters.command("addbal"))
async def add_balance(_, message: Message):
    if message.from_user.id != BALANCE_GIVER_ID:
        return await message.reply_text("❌ You are not allowed to give balance.")

    parts = message.text.split()
    amount = None
    target_id = None

    for p in parts:
        if p.isdigit():
            amount = int(p)
        elif p.startswith("@"):
            user = await user_collection.find_one({"username": p[1:]})
            if user:
                target_id = user["id"]

    if not amount or not target_id:
        return await message.reply_text(
            "❌ Usage:\n"
            "/addbal <amount> @username\n"
            "/addbal @username <amount>"
        )

    await user_collection.update_one(
        {"id": target_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )

    await message.reply_text(
        f"✅ Added <b>{amount}</b> coins successfully.",
        parse_mode=ParseMode.HTML
    )


# ─────────────────────────────────
# PAY
# ─────────────────────────────────
@app.on_message(filters.command("pay"))
async def pay_cmd(_, message: Message):
    sender = await ensure_user(message.from_user)
    parts = message.text.split()

    amount = None
    receiver_id = None

    if message.reply_to_message:
        receiver_id = message.reply_to_message.from_user.id
        for p in parts:
            if p.isdigit():
                amount = int(p)
    else:
        for p in parts:
            if p.isdigit():
                amount = int(p)
            elif p.startswith("@"):
                user = await user_collection.find_one({"username": p[1:]})
                if user:
                    receiver_id = user["id"]

    if not amount or not receiver_id:
        return await message.reply_text(
            "❌ Usage:\n"
            "/pay <amount> @username\n"
            "/pay @username <amount>"
        )

    if sender["balance"] < amount:
        return await message.reply_text("❌ Insufficient balance.")

    await user_collection.update_one(
        {"id": sender["id"]},
        {"$inc": {"balance": -amount}}
    )

    await user_collection.update_one(
        {"id": receiver_id},
        {"$inc": {"balance": amount}},
        upsert=True
    )

    await message.reply_text(
        f"✅ Paid <b>{amount}</b> coins successfully.",
        parse_mode=ParseMode.HTML
    )


# ─────────────────────────────────
# HOURLY
# ─────────────────────────────────
@app.on_message(filters.command("hourly"))
async def hourly_cmd(_, message: Message):
    user = await ensure_user(message.from_user)

    now = int(time.time())
    if now - user["last_hourly"] < HOURLY_COOLDOWN:
        wait = HOURLY_COOLDOWN - (now - user["last_hourly"])
        return await message.reply_text(
            f"⏳ Come back in {wait // 60} minutes."
        )

    await user_collection.update_one(
        {"id": user["id"]},
        {
            "$inc": {"balance": HOURLY_AMOUNT},
            "$set": {"last_hourly": now}
        }
    )

    await message.reply_text(
        f"✅ Hourly reward claimed!\n💰 +{HOURLY_AMOUNT} coins"
    )


# ─────────────────────────────────
# DAILY
# ─────────────────────────────────
@app.on_message(filters.command("daily"))
async def daily_cmd(_, message: Message):
    user = await ensure_user(message.from_user)

    now = int(time.time())
    if now - user["last_daily"] < DAILY_COOLDOWN:
        wait = DAILY_COOLDOWN - (now - user["last_daily"])
        return await message.reply_text(
            f"⏳ Come back in {wait // 3600} hours."
        )

    await user_collection.update_one(
        {"id": user["id"]},
        {
            "$inc": {"balance": DAILY_AMOUNT},
            "$set": {"last_daily": now}
        }
    )

    await message.reply_text(
        f"🎁 Daily reward claimed!\n💰 +{DAILY_AMOUNT} coins"
    )
