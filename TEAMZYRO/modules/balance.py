
from pyrogram import filters
from pyrogram.types import Message
import html

from TEAMZYRO import app, user_collection

# 🔒 ONLY THIS USER CAN ADD BALANCE
BALANCE_GIVER_ID = 1334658171


# ─────────────────────────────────────────────
# 🔧 ENSURE USER EXISTS
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# 💰 BALANCE COMMAND
# ─────────────────────────────────────────────
@app.on_message(filters.command("balance"))
async def balance_cmd(_, message: Message):
    user = await ensure_user(message.from_user)

    await message.reply_text(
        f"💰 <b>{html.escape(message.from_user.first_name)}'s Balance</b>\n\n"
        f"🪙 Coins: <b>{user.get('balance', 0)}</b>\n"
        f"🎟 Tokens: <b>{user.get('tokens', 0)}</b>",
        parse_mode="html"
    )


# ─────────────────────────────────────────────
# 💸 PAY COMMAND
# Usage:
# /pay 100 @username
# /pay 100 (reply)
# ─────────────────────────────────────────────
@app.on_message(filters.command("pay"))
async def pay_cmd(_, message: Message):
    sender = await ensure_user(message.from_user)
    args = message.command

    if len(args) < 2:
        return await message.reply_text(
            "❌ Usage:\n/pay <amount> @username\nor reply:\n/pay <amount>"
        )

    # amount
    try:
        amount = int(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Invalid amount.")

    # get receiver
    receiver_id = None

    if message.reply_to_message:
        receiver_id = message.reply_to_message.from_user.id
    elif len(args) >= 3:
        username = args[2].lstrip("@")
        user = await user_collection.find_one({"username": username})
        if not user:
            return await message.reply_text("❌ User not found.")
        receiver_id = user["id"]
    else:
        return await message.reply_text(
            "❌ Mention a user or reply to a message."
        )

    if receiver_id == sender["id"]:
        return await message.reply_text("❌ You cannot pay yourself.")

    if sender["balance"] < amount:
        return await message.reply_text("❌ Insufficient balance.")

    # ensure receiver exists
    receiver = await user_collection.find_one({"id": receiver_id})
    if not receiver:
        receiver = {
            "id": receiver_id,
            "balance": 0,
            "tokens": 0,
            "characters": []
        }
        await user_collection.insert_one(receiver)

    # transfer
    await user_collection.update_one(
        {"id": sender["id"]},
        {"$inc": {"balance": -amount}}
    )
    await user_collection.update_one(
        {"id": receiver_id},
        {"$inc": {"balance": amount}}
    )

    await message.reply_text(
        f"✅ Paid <b>{amount}</b> coins successfully.",
        parse_mode="html"
    )

    try:
        await app.send_message(
            receiver_id,
            f"🎉 You received <b>{amount}</b> coins from "
            f"<b>{html.escape(message.from_user.first_name)}</b>",
            parse_mode="html"
        )
    except:
        pass


# ─────────────────────────────────────────────
# ➕ ADD BALANCE (ONLY ONE USER)
# ─────────────────────────────────────────────
@app.on_message(filters.command("addbal"))
async def add_balance(_, message: Message):
    if message.from_user.id != BALANCE_GIVER_ID:
        return await message.reply_text("❌ You are not allowed.")

    if len(message.command) < 3:
        return await message.reply_text(
            "Usage:\n/addbal user_id amount"
        )

    try:
        uid = int(message.command[1])
        amount = int(message.command[2])
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Invalid user ID or amount.")

    await user_collection.update_one(
        {"id": uid},
        {"$inc": {"balance": amount}},
        upsert=True
    )

    await message.reply_text(
        f"✅ Added <b>{amount}</b> coins to <code>{uid}</code>",
        parse_mode="html"
    )
