import time
import html
from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from TEAMZYRO import app, user_collection

# ─── CONFIG ───────────────────────────────
HOURLY_REWARD = 100
DAILY_REWARD = 500

HOURLY_COOLDOWN = 60 * 60        # 1 hour
DAILY_COOLDOWN = 60 * 60 * 24    # 24 hours


# ─── ENSURE USER (AUTO-FIX OLD USERS) ──────
async def ensure_user(user):
    data = await user_collection.find_one({"id": user.id})
    now = int(time.time())

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

    # Fix old datetime fields
    lh = data.get("last_hourly", 0)
    ld = data.get("last_daily", 0)

    if isinstance(lh, datetime):
        updates["last_hourly"] = int(lh.timestamp())
    elif not isinstance(lh, int):
        updates["last_hourly"] = 0

    if isinstance(ld, datetime):
        updates["last_daily"] = int(ld.timestamp())
    elif not isinstance(ld, int):
        updates["last_daily"] = 0

    # Ensure core fields
    for key, default in {
        "balance": 0,
        "tokens": 0,
        "characters": []
    }.items():
        if key not in data:
            updates[key] = default

    if data.get("first_name") != user.first_name:
        updates["first_name"] = user.first_name
    if data.get("username") != user.username:
        updates["username"] = user.username

    if updates:
        await user_collection.update_one({"id": user.id}, {"$set": updates})
        data.update(updates)

    return data


# ─── BALANCE ──────────────────────────────
@app.on_message(filters.command("balance"))
async def balance_cmd(_, message: Message):
    user = await ensure_user(message.from_user)

    await message.reply_text(
        f"💰 <b>{html.escape(user['first_name'])}'s Balance</b>\n\n"
        f"🪙 Coins: <b>{user['balance']}</b>\n"
        f"🎟 Tokens: <b>{user['tokens']}</b>",
        parse_mode=ParseMode.HTML
    )


# ─── HOURLY ───────────────────────────────
@app.on_message(filters.command("hourly"))
async def hourly_cmd(_, message: Message):
    user = await ensure_user(message.from_user)
    now = int(time.time())

    if now - user["last_hourly"] < HOURLY_COOLDOWN:
        remaining = HOURLY_COOLDOWN - (now - user["last_hourly"])
        m, s = divmod(remaining, 60)
        return await message.reply_text(
            f"⏳ Try again in {m}m {s}s"
        )

    await user_collection.update_one(
        {"id": user["id"]},
        {
            "$inc": {"balance": HOURLY_REWARD},
            "$set": {"last_hourly": now}
        }
    )

    await message.reply_text(
        f"🪙 You received <b>{HOURLY_REWARD}</b> coins!",
        parse_mode=ParseMode.HTML
    )


# ─── DAILY ────────────────────────────────
@app.on_message(filters.command("daily"))
async def daily_cmd(_, message: Message):
    user = await ensure_user(message.from_user)
    now = int(time.time())

    if now - user["last_daily"] < DAILY_COOLDOWN:
        remaining = DAILY_COOLDOWN - (now - user["last_daily"])
        h = remaining // 3600
        return await message.reply_text(
            f"⏳ Come back in {h}h"
        )

    await user_collection.update_one(
        {"id": user["id"]},
        {
            "$inc": {"balance": DAILY_REWARD},
            "$set": {"last_daily": now}
        }
    )

    await message.reply_text(
        f"🌞 Daily reward claimed!\n🪙 +{DAILY_REWARD} coins",
        parse_mode=ParseMode.HTML
    )


# ─── PAY ──────────────────────────────────
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
            "❌ Usage:\n/pay <amount> @username\n/pay @username <amount>"
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
