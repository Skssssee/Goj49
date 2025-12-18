from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random
import asyncio
import html

from TEAMZYRO import app as Client
from TEAMZYRO import user_collection, top_global_groups_collection

PHOTO_URL = ["https://files.catbox.moe/9j8e6b.jpg"]


# ─────────────────────────────────────────────
# /rank
# ─────────────────────────────────────────────
@Client.on_message(filters.command("rank"))
async def rank(client, message):
    cursor = user_collection.find(
        {}, {"_id": 0, "id": 1, "first_name": 1, "characters": 1}
    )

    users = await cursor.to_list(length=None)
    users.sort(key=lambda x: len(x.get("characters", [])), reverse=True)
    users = users[:10]

    caption = "<b>TOP 10 USERS WITH MOST CHARACTERS</b>\n\n"
    for i, u in enumerate(users, start=1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"{html.escape(u.get('first_name','Unknown'))}</a> "
            f"➜ {len(u.get('characters', []))}\n"
        )

    await message.reply_photo(
        photo=random.choice(PHOTO_URL),
        caption=caption,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=rank_buttons("top")
    )


# ─────────────────────────────────────────────
# BUTTON BUILDER
# ─────────────────────────────────────────────
def rank_buttons(active):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("TOP 🥀" if active == "top" else "TOP", callback_data="top"),
                InlineKeyboardButton(
                    "TOP GROUP 🥀" if active == "top_group" else "TOP GROUP",
                    callback_data="top_group"
                ),
            ],
            [
                InlineKeyboardButton("MTOP 🥀" if active == "mtop" else "MTOP", callback_data="mtop"),
                InlineKeyboardButton("TOKENS 🥀" if active == "tokens" else "TOKENS", callback_data="tokens"),
            ],
        ]
    )


# ─────────────────────────────────────────────
# TOP USERS (CHARACTERS)
# ─────────────────────────────────────────────
@Client.on_callback_query(filters.regex("^top$"))
async def top_cb(client, cq):
    users = await user_collection.find(
        {}, {"id": 1, "first_name": 1, "characters": 1}
    ).to_list(None)

    users.sort(key=lambda x: len(x.get("characters", [])), reverse=True)
    users = users[:10]

    caption = "<b>TOP 10 USERS WITH MOST CHARACTERS</b>\n\n"
    for i, u in enumerate(users, start=1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"{html.escape(u.get('first_name','Unknown'))}</a> "
            f"➜ {len(u.get('characters', []))}\n"
        )

    if cq.message.caption != caption:
        await cq.edit_message_caption(
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=rank_buttons("top")
        )


# ─────────────────────────────────────────────
# TOP GROUPS
# ─────────────────────────────────────────────
@Client.on_callback_query(filters.regex("^top_group$"))
async def top_group_cb(client, cq):
    groups = await top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]).to_list(10)

    caption = "<b>TOP 10 GROUPS</b>\n\n"
    for i, g in enumerate(groups, start=1):
        caption += f"{i}. {html.escape(g.get('group_name','Unknown'))} ➜ {g['count']}\n"

    if cq.message.caption != caption:
        await cq.edit_message_caption(
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=rank_buttons("top_group")
        )


# ─────────────────────────────────────────────
# MTOP (BALANCE — FIXED)
# ─────────────────────────────────────────────
@Client.on_callback_query(filters.regex("^mtop$"))
async def mtop_cb(client, cq):
    users = await user_collection.find(
        {"balance": {"$exists": True}},
        {"id": 1, "first_name": 1, "balance": 1}
    ).sort("balance", -1).limit(10).to_list(10)

    caption = "<b>MTOP LEADERBOARD</b>\n\n"
    for i, u in enumerate(users, start=1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"{html.escape(u.get('first_name','Unknown'))}</a> "
            f"➜ 💰 {u.get('balance',0)}\n"
        )

    if cq.message.caption != caption:
        await cq.edit_message_caption(
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=rank_buttons("mtop")
        )


# ─────────────────────────────────────────────
# TOKENS
# ─────────────────────────────────────────────
@Client.on_callback_query(filters.regex("^tokens$"))
async def tokens_cb(client, cq):
    users = await user_collection.find(
        {"tokens": {"$exists": True}},
        {"id": 1, "first_name": 1, "tokens": 1}
    ).sort("tokens", -1).limit(10).to_list(10)

    caption = "<b>TOKENS LEADERBOARD</b>\n\n"
    for i, u in enumerate(users, start=1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"{html.escape(u.get('first_name','Unknown'))}</a> "
            f"➜ 🎟 {u.get('tokens',0)}\n"
        )

    if cq.message.caption != caption:
        await cq.edit_message_caption(
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=rank_buttons("tokens")
        )
