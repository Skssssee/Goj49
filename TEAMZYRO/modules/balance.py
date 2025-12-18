from TEAMZYRO import *
from pyrogram import Client, filters
from pyrogram.types import Message
import html

# 🔹 Always read coins, NOT balance
async def get_balance(user_id):
    user = await user_collection.find_one(
        {"id": user_id},
        {"coins": 1, "tokens": 1}
    )
    if user:
        return user.get("coins", 0), user.get("tokens", 0)
    return 0, 0


@app.on_message(filters.command("balance"))
async def balance(client: Client, message: Message):
    coins, tokens = await get_balance(message.from_user.id)

    await message.reply_text(
        f"{html.escape(message.from_user.first_name)}\n"
        f"◈⌠ {coins} coins ⌡\n"
        f"◈⌠ {tokens} tokens ⌡"
    )
