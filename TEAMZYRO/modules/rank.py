from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import html
import random

from TEAMZYRO import app as Client
from TEAMZYRO import user_collection

PHOTO_URL = ["https://files.catbox.moe/9j8e6b.jpg"]


@Client.on_message(filters.command("rank"))
async def rank_cmd(client, message):
    caption = "<b>MTOP LEADERBOARD</b>\n\n"
    caption += "Click buttons below ⬇️"

    buttons = [
        [
            InlineKeyboardButton("MTOP 🥀", callback_data="mtop"),
            InlineKeyboardButton("TOKENS 🥀", callback_data="tokens")
        ]
    ]

    await message.reply_photo(
        photo=random.choice(PHOTO_URL),
        caption=caption,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


@Client.on_callback_query(filters.regex("^mtop$"))
async def mtop_callback(client, cq):
    users = await user_collection.find(
        {"balance": {"$exists": True}},
        {"id": 1, "first_name": 1, "balance": 1}
    ).sort("balance", -1).limit(10).to_list(10)

    caption = "<b>MTOP LEADERBOARD</b>\n\n"

    for i, u in enumerate(users, 1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"{html.escape(u.get('first_name','Unknown'))}</a> "
            f"➜ 💰 {u.get('balance',0)}\n"
        )

    if cq.message.caption != caption:
        await cq.edit_message_caption(
            caption=caption,
            parse_mode=enums.ParseMode.HTML
        )


@Client.on_callback_query(filters.regex("^tokens$"))
async def tokens_callback(client, cq):
    users = await user_collection.find(
        {"tokens": {"$exists": True}},
        {"id": 1, "first_name": 1, "tokens": 1}
    ).sort("tokens", -1).limit(10).to_list(10)

    caption = "<b>TOKENS LEADERBOARD</b>\n\n"

    for i, u in enumerate(users, 1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"{html.escape(u.get('first_name','Unknown'))}</a> "
            f"➜ 🎟 {u.get('tokens',0)}\n"
        )

    if cq.message.caption != caption:
        await cq.edit_message_caption(
            caption=caption,
            parse_mode=enums.ParseMode.HTML
        )
