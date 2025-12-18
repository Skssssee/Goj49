
from pyrogram import filters
from pyrogram.types import Message
from TEAMZYRO import app, user_collection
import html

# 🔒 ONLY THIS USER CAN ADD BALANCE
BALANCE_GIVER_ID = 1334658171


# ─── GET OR CREATE USER ─────────────────────────────
async def get_user(user):
    data = await user_collection.find_one({"id": user.id})
    if not data:
        data = {
            "id": user.id,
            "first_name": user.first_name,
            "username": user.username,
            "coins": 0,
            "tokens": 0,
            "characters": []
        }
        await user_collection.insert_one(data)
    else:
        # auto-fix old users
        if "coins" not in data:
            await user_collection.update_one(
                {"id": user.id},
                {"$set": {"coins": 0}}
            )
            data["coins"] = 0
    return data


# ─── BALANCE ────────────────────────────────────────
@app.on_message(filters.command("balance"))
async def balance_cmd(_, message: Message):
    user = await get_user(message.from_user)
    await message.reply_text(
        f"💰 <b>{html.escape(message.from_user.first_name)}'s Balance</b>\n\n"
        f"🪙 Coins: <b>{user['coins']}</b>\n"
        f"🎟 Tokens: <b>{user.get('tokens', 0)}</b>",
        parse_mode="html"
    )


# ─── PAY COMMAND ────────────────────────────────────
@app.on_message(filters.command("pay"))
async def pay_cmd(_, message: Message):
    sender = await get_user(message.from_user)
    args = message.command

    if len(args) < 2 and not message.reply_to_message:
        return await message.reply_text(
            "❌ Usage:\n"
            "/pay <amount> @username\n"
            "/pay @username <amount>\n"
            "or reply: /pay <amount>"
        )

    amount = None
    target = None

    # reply method
    if message.reply_to_message:
        try:
            amount = int(args[1])
        except:
            return await message.reply_text("❌ Invalid amount.")
        target = message.reply_to_message.from_user

    else:
        # detect order
        for part in args[1:]:
            if part.isdigit():
                amount = int(part)
            elif part.startswith("@"):
                target = await app.get_users(part)

    if not amount or not target:
        return await message.reply_text("❌ Invalid amount or user.")

    if amount <= 0:
        return await message.reply_text("❌ Amount must be positive.")

    if sender["coins"] < amount:
        return await message.reply_text("❌ Insufficient balance.")

    # ensure receiver exists
    receiver = await user_collection.find_one({"id": target.id})
    if not receiver:
        await user_collection.insert_one({
            "id": target.id,
            "first_name": target.first_name,
            "username": target.username,
            "coins": 0,
            "tokens": 0,
            "characters": []
        })

    # transfer
    await user_collection.update_one(
        {"id": sender["id"]},
        {"$inc": {"coins": -amount}}
    )
    await user_collection.update_one(
        {"id": target.id},
        {"$inc": {"coins": amount}}
    )

    await message.reply_text(
        f"✅ Paid <b>{amount}</b> coins to <b>{html.escape(target.first_name)}</b>",
        parse_mode="html"
    )

    await app.send_message(
        target.id,
        f"🎉 You received <b>{amount}</b> coins from <b>{html.escape(message.from_user.first_name)}</b>",
        parse_mode="html"
    )


# ─── ADD BALANCE (ONLY SPECIFIC USER) ───────────────
@app.on_message(filters.command("addbal"))
async def addbal_cmd(_, message: Message):

    if message.from_user.id != BALANCE_GIVER_ID:
        return await message.reply_text("❌ You are not allowed to add coins.")

    args = message.command

    if len(args) < 3 and not message.reply_to_message:
        return await message.reply_text(
            "❌ Usage:\n"
            "/addbal <amount> @username\n"
            "or reply: /addbal <amount>"
        )

    try:
        amount = int(args[1])
    except:
        return await message.reply_text("❌ Invalid amount.")

    if amount <= 0:
        return await message.reply_text("❌ Amount must be positive.")

    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        target = await app.get_users(args[2])

    await user_collection.update_one(
        {"id": target.id},
        {"$inc": {"coins": amount}},
        upsert=True
    )

    await message.reply_text(
        f"✅ Added <b>{amount}</b> coins to <b>{html.escape(target.first_name)}</b>",
        parse_mode="html"
    )
