
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random
import html
import asyncio

from TEAMZYRO import app
from TEAMZYRO import user_collection, top_global_groups_collection

PHOTO_URL = ["https://files.catbox.moe/9j8e6b.jpg"]


# ─────────────────────────────────────────────
# MAIN /rank COMMAND
# ─────────────────────────────────────────────
@app.on_message(filters.command("rank"))
async def rank_cmd(client, message):
    caption = await build_mtop_caption()

    await message.reply_photo(
        photo=random.choice(PHOTO_URL),
        caption=caption,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=rank_buttons("mtop")
    )


# ─────────────────────────────────────────────
# BUTTON LAYOUT
# ─────────────────────────────────────────────
def rank_buttons(active):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🏆 MTOP" if active == "mtop" else "MTOP",
                    callback_data="rank_mtop"
                ),
                InlineKeyboardButton(
                    "🪙 TOKENS" if active == "tokens" else "TOKENS",
                    callback_data="rank_tokens"
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 TOP USERS" if active == "top" else "TOP USERS",
                    callback_data="rank_top"
                ),
                InlineKeyboardButton(
                    "🏘 TOP GROUPS" if active == "groups" else "TOP GROUPS",
                    callback_data="rank_groups"
                )
            ]
        ]
    )


# ─────────────────────────────────────────────
# BUILD CAPTIONS
# ─────────────────────────────────────────────
async def build_mtop_caption():
    users = await user_collection.find(
        {"balance": {"$gt": 0}}
    ).sort("balance", -1).limit(10).to_list(10)

    text = "<b>🏆 MTOP LEADERBOARD (COINS)</b>\n\n"

    if not users:
        return text + "No users with balance yet."

    for i, u in enumerate(users, 1):
        name = html.escape(u.get("first_name", "Unknown"))
        bal = u.get("balance", 0)
        uid = u.get("id")
        text += f"{i}. <a href='tg://user?id={uid}'>{name}</a> → 💰 <b>{bal}</b>\n"

    return text


async def build_tokens_caption():
    users = await user_collection.find(
        {"tokens": {"$gt": 0}}
    ).sort("tokens", -1).limit(10).to_list(10)

    text = "<b>🪙 TOKENS LEADERBOARD</b>\n\n"

    if not users:
        return text + "No users with tokens yet."

    for i, u in enumerate(users, 1):
        name = html.escape(u.get("first_name", "Unknown"))
        tokens = u.get("tokens", 0)
        uid = u.get("id")
        text += f"{i}. <a href='tg://user?id={uid}'>{name}</a> → 🪙 <b>{tokens}</b>\n"

    return text


async def build_top_users_caption():
    users = await user_collection.find(
        {"characters": {"$exists": True}}
    ).to_list(None)

    users.sort(key=lambda x: len(x.get("characters", [])), reverse=True)
    users = users[:10]

    text = "<b>👥 TOP USERS BY CHARACTERS</b>\n\n"

    if not users:
        return text + "No data available."

    for i, u in enumerate(users, 1):
        name = html.escape(u.get("first_name", "Unknown"))
        count = len(u.get("characters", []))
        uid = u.get("id")
        text += f"{i}. <a href='tg://user?id={uid}'>{name}</a> → 🎴 <b>{count}</b>\n"

    return text


async def build_groups_caption():
    groups = await top_global_groups_collection.aggregate(
        [
            {"$project": {"group_name": 1, "count": 1}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
    ).to_list(10)

    text = "<b>🏘 TOP GROUPS</b>\n\n"

    if not groups:
        return text + "No group data available."

    for i, g in enumerate(groups, 1):
        name = html.escape(g.get("group_name", "Unknown"))
        count = g.get("count", 0)
        text += f"{i}. {name} → 🎴 <b>{count}</b>\n"

    return text


# ─────────────────────────────────────────────
# CALLBACK HANDLER
# ─────────────────────────────────────────────
@app.on_callback_query(filters.regex("^rank_"))
async def rank_callback(client, cq):
    action = cq.data.replace("rank_", "")

    if action == "mtop":
        caption = await build_mtop_caption()
    elif action == "tokens":
        caption = await build_tokens_caption()
    elif action == "top":
        caption = await build_top_users_caption()
    elif action == "groups":
        caption = await build_groups_caption()
    else:
        return await cq.answer("Unknown action")

    try:
        await cq.message.edit_caption(
            caption=caption,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=rank_buttons(action)
        )
    except Exception:
        # Prevent MESSAGE_NOT_MODIFIED crash
        pass

    await cq.answer()
