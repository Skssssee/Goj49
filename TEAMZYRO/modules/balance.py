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


async def resolve_username(client: Client, username: str):
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

    await message.reply_text(
        f"👤 {html.escape(message.from_user.first_name)}\n\n"
        f"💰 Coins: `{user.get('balance', 0)}`\n"
        f"🪙 Tokens: `{user.get('tokens', 0)}`"
    )


# ─────────────────────────────────────────────
# /pay (SMART VERSION)
# ─────────────────────────────────────────────

@app.on_message(filters.command("pay"))
async def pay_cmd(client: Client, message: Message):
    args = message.command
    sender = await get_or_create_user(message.from_user)

    receiver_id = None
    receiver_name = None
    amount = None

    # ─── CASE 1: Reply + /pay amount
    if message.reply_to_message and len(args) == 2:
        receiver = message.reply_to_message.from_user
        receiver_id = receiver.id
        receiver_name = receiver.first_name

        try:
            amount = int(args[1])
        except ValueError:
            return await message.reply_text("❌ Invalid amount.")

    # ─── CASE 2: /pay amount @username
    elif len(args) == 3 and args[1].isdigit():
        amount = int(args[1])
        receiver_id, receiver_name = await resolve_username(client, args[2])

    # ─── CASE 3: /pay @username amount
    elif len(args) == 3 and args[2].isdigit():
        amount = int(args[2])
        receiver_id, receiver_name = await resolve_username(client, args[1])

    else:
        return await message.reply_text(
            "❌ Invalid format.\n\n"
            "✅ Correct usage:\n"
            "`/pay 78 @username`\n"
            "`/pay @username 78`\n"
            "or reply + `/pay 78`"
        )

    # ─── VALIDATION
    if not receiver_id or amount is None or amount <= 0:
        return await message.reply_text("❌ Invalid amount or user.")

    if receiver_id == sender["id"]:
        return await message.reply_text("❌ You cannot pay yourself.")

    if sender.get("balance", 0) < amount:
        return await message.reply_text("❌ Insufficient balance.")

    # ─── ENSURE RECEIVER EXISTS
    receiver = await user_collection.find_one({"id": receiver_id})
    if not receiver:
        await user_collection.insert_one({
            "id": receiver_id,
            "first_name": receiver_name,
            "balance": 0,
            "tokens": 0
        })

    # ─── UPDATE BALANCES
    await user_collection.update_one(
        {"id": sender["id"]},
        {"$inc": {"balance": -amount}}
    )

    await user_collection.update_one(
        {"id": receiver_id},
        {"$inc": {"balance": amount}}
    )

    await message.reply_text(
        f"✅ Paid **{amount} coins** to "
        f"<a href='tg://user?id={receiver_id}'>{html.escape(receiver_name)}</a>",
        parse_mode="html"
    )

    try:
        await client.send_message(
            receiver_id,
            f"🎉 You received **{amount} coins** from "
            f"{html.escape(message.from_user.first_name)}",
            parse_mode="html"
        )
    except:
        pass
