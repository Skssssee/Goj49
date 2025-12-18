# rank.py
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random, asyncio, html
from TEAMZYRO import app, user_collection, top_global_groups_collection

PHOTO_URL = ["https://files.catbox.moe/9j8e6b.jpg"]

@app.on_message(filters.command("rank"))
async def rank(client, message):
    cursor = user_collection.find({}, {"id": 1, "first_name": 1, "characters": 1})
    data = await cursor.to_list(length=None)

    data.sort(key=lambda x: len(x.get("characters", [])), reverse=True)
    data = data[:10]

    caption = "<b>ᴛᴏᴘ 10 ᴜsᴇʀs ʙʏ ᴄʜᴀʀᴀᴄᴛᴇʀs</b>\n\n"
    for i, u in enumerate(data, 1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','Unknown'))}</b></a> ➾ "
            f"{len(u.get('characters', []))}\n"
        )

    buttons = [
        [InlineKeyboardButton("MTOP 🪙", callback_data="mtop")],
        [InlineKeyboardButton("TOKENS 🧿", callback_data="tokens")]
    ]

    await message.reply_photo(
        photo=random.choice(PHOTO_URL),
        caption=caption,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex("^mtop$"))
async def mtop(_, cq):
    users = await user_collection.find().sort("coins", -1).limit(10).to_list(10)

    caption = "<b>🏆 TOP 10 USERS BY COINS</b>\n\n"
    for i, u in enumerate(users, 1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','User'))}</b></a> "
            f"➾ 💰 {u.get('coins',0)}\n"
        )

    await cq.edit_message_caption(caption, parse_mode=enums.ParseMode.HTML)

@app.on_callback_query(filters.regex("^tokens$"))
async def tokens(_, cq):
    users = await user_collection.find().sort("tokens", -1).limit(10).to_list(10)

    caption = "<b>🏆 TOP 10 USERS BY TOKENS</b>\n\n"
    for i, u in enumerate(users, 1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','User'))}</b></a> "
            f"➾ 🪙 {u.get('tokens',0)}\n"
        )

    await cq.edit_message_caption(caption, parse_mode=enums.ParseMode.HTML)
