from pyrogram import filters
from pyrogram.types import Message
import html

from TEAMZYRO import app, user_collection

# 🔐 ONLY THIS USER CAN GIVE MONEY
BALANCE_GIVER_ID = 1334658171


# ─────────────────────────────
# Ensure user exists
# ─────────────────────────────
async def ensure_user(user):
    data = await user_collection.find_one({"id": user.id})
    if not data:
        data = {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": 0,
            "tokens": 0,
            "characters": []
        }
        await user_collection.insert_one(data)
    return data


# ─────────────────────────────
# BALANCE
# ─────────────────────────────
@app.on_message(filters.command("balance"))
async def balance_cmd(_, message: Message):
    user = await ensure_user(message.from_user)

    await message.reply_text(
        f"💰 <b>{html.escape(message.from_user.first_name)}'s Balance</b>\n\n"
        f"🪙 Coins: <b>{user.get('balance', 0)}</b>\n"
        f"🎟 Tokens: <b>{user.get('tokens', 0)}</b>",
        parse_mode="html"
    )


# ─────────────────────────────
# ADD BALANCE (FIXED)
# ─────────────────────────────
@app.on_message(filters.command("addbal"))
async def add_balance(_, message: Message):
    if message.from_user.id != BALANCE_GIVER_ID:
        return await message.reply_text("❌ You are not allowed to give balance.")

    parts = message.text.split()

    amount = None
    target_id = None

    for p in parts:
        # amount
        if p.isdigit():
            amount = int(p)

        # username
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
        f"✅ Successfully added <b>{amount}</b> coins.",
        parse_mode="html"
    )


# ─────────────────────────────
# PAY (ALREADY FIXED)
# ─────────────────────────────
@app.on_message(filters.command("pay"))
async def pay_cmd(_, message: Message):
    sender = await ensure_user(message.from_user)
    parts = message.text.split()

    amount = None
    receiver_id = None

    # reply mode
    if message.reply_to_message:
        for p in parts:
            if p.isdigit():
                amount = int(p)
        receiver_id = message.reply_to_message.from_user.id

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

    if receiver_id == sender["id"]:
        return await message.reply_text("❌ You cannot pay yourself.")

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
        parse_mode="html"
    )
