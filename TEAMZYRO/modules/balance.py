from pyrogram import Client, filters
from pyrogram.types import Message
import html

from TEAMZYRO import app, user_collection


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

async def get_or_create_user(user):
    data = await user_collection.find_one({"id": user.id})
    if not data:
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "balance": 0,
            "tokens": 0
        }
        await user_collection.insert_one(data)
    return data


async def username_to_id(client: Client, username: str):
    username = username.lstrip("@")
    try:
        user = await client.get_users(username)
        return user.id, user.first_name
    except Exception:
        return None, None


# ─────────────────────────────────────────────
# /balance
# ─────────────────────────────────────────────

@app.on_message(filters.command("balance"))
async def balance_cmd(client: Client, message: Message):
    user = await get_or_create_user(message.from_user)

    coins = user.get("balance", 0)
    tokens = user.get("tokens", 0)

    await message.reply_text(
        f"👤 {html.escape(message.from_user.first_name)}\n\n"
        f"💰 Coins: `{coins}`\n"
        f"🪙 Tokens: `{tokens}`"
    )


# ─────────────────────────────────────────────
# /pay
# ─────────────────────────────────────────────

@app.on_message(filters.command("pay"))
async def pay_cmd(client: Client, message: Message):
    args = message.command

    if len(args) < 2:
        return await message.reply_text(
            "❌ Usage:\n"
            "`/pay amount @username`\n"
            "or reply to a user"
        )

    # Validate amount
    try:
        amount = int(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Invalid amount.")

    sender = await get_or_create_user(message.from_user)
    sender_balance = sender.get("balance", 0)

    if sender_balance < amount:
        return await message.reply_text("❌ Insufficient balance.")

    # ─── GET RECEIVER ─────────────────────────
    if message.reply_to_message:
        receiver_user = message.reply_to_message.from_user
        receiver_id = receiver_user.id
        receiver_name = receiver_user.first_name
    elif len(args) >= 3:
        receiver_id, receiver_name = await username_to_id(client, args[2])
        if not receiver_id:
            return await message.reply_text("❌ User not found.")
    else:
        return await message.reply_text("❌ Specify a user or reply.")

    # Prevent self-pay
    if receiver_id == message.from_user.id:
        return await message.reply_text("❌ You cannot pay yourself.")

    # Ensure receiver exists
    receiver = await user_collection.find_one({"id": receiver_id})
    if not receiver:
        await user_collection.insert_one({
            "id": receiver_id,
            "first_name": receiver_name,
            "balance": 0,
            "tokens": 0
        })

    # ─── UPDATE BALANCES ──────────────────────
    await user_collection.update_one(
        {"id": sender["id"]},
        {"$inc": {"balance": -amount}}
    )

    await user_collection.update_one(
        {"id": receiver_id},
        {"$inc": {"balance": amount}}
    )

    await message.reply_text(
        f"✅ You paid **{amount} coins** to "
        f"<a href='tg://user?id={receiver_id}'>{html.escape(receiver_name)}</a>.",
        parse_mode="html"
    )

    try:
        await client.send_message(
            receiver_id,
            f"🎉 You received **{amount} coins** from "
            f"{html.escape(message.from_user.first_name)}.",
            parse_mode="html"
        )
    except Exception:
        pass
