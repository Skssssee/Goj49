
from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random
import asyncio
import html
from TEAMZYRO import app
from TEAMZYRO import user_collection, top_global_groups_collection

PHOTO_URL = ["https://files.catbox.moe/9j8e6b.jpg"]

# ─── STATIC KEYBOARD (IMPORTANT) ────────────────────
def rank_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("ᴛᴏᴘ🥀", callback_data="top"),
                InlineKeyboardButton("ᴛᴏᴘ ɢʀᴏᴜᴘ🥀", callback_data="top_group"),
            ],
            [
                InlineKeyboardButton("ᴍᴛᴏᴘ🥀", callback_data="mtop"),
                InlineKeyboardButton("ᴛᴏᴋᴇɴs🥀", callback_data="tokens"),
            ],
        ]
    )

# ─── MAIN RANK ──────────────────────────────────────
@app.on_message(filters.command("rank"))
async def rank(_, message):
    users = await user_collection.find(
        {}, {"_id": 0, "id": 1, "first_name": 1, "characters": 1}
    ).to_list(length=None)

    users.sort(key=lambda x: len(x.get("characters", [])), reverse=True)
    users = users[:10]

    caption = "<b>ᴛᴏᴘ 10 ᴜsᴇʀs ᴡɪᴛʜ ᴍᴏsᴛ ᴄʜᴀʀᴀᴄᴛᴇʀs</b>\n\n"
    for i, u in enumerate(users, 1):
        uid = u.get("id")
        name = html.escape(u.get("first_name", "Unknown"))[:15]
        count = len(u.get("characters", []))
        caption += f"{i}. <a href='tg://user?id={uid}'><b>{name}</b></a> ➾ <b>{count}</b>\n"

    await message.reply_photo(
        photo=random.choice(PHOTO_URL),
        caption=caption,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=rank_keyboard()
    )

# ─── EDIT HELPER ────────────────────────────────────
async def edit_rank(callback_query, caption):
    await callback_query.edit_message_caption(
        caption=caption,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=rank_keyboard()
    )

# ─── TOP USERS ──────────────────────────────────────
@app.on_callback_query(filters.regex("^top$"))
async def top_cb(_, cq):
    await asyncio.sleep(0.5)
    users = await user_collection.find(
        {}, {"id": 1, "first_name": 1, "characters": 1}
    ).to_list(length=None)

    users.sort(key=lambda x: len(x.get("characters", [])), reverse=True)
    users = users[:10]

    caption = "<b>ᴛᴏᴘ 10 ᴜsᴇʀs ᴡɪᴛʜ ᴍᴏsᴛ ᴄʜᴀʀᴀᴄᴛᴇʀs</b>\n\n"
    for i, u in enumerate(users, 1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','Unknown'))}</b></a>"
            f" ➾ <b>{len(u.get('characters', []))}</b>\n"
        )

    await edit_rank(cq, caption)

# ─── TOP GROUPS ─────────────────────────────────────
@app.on_callback_query(filters.regex("^top_group$"))
async def top_group_cb(_, cq):
    await asyncio.sleep(0.5)
    groups = await top_global_groups_collection.aggregate(
        [
            {"$project": {"group_name": 1, "count": 1}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
    ).to_list(10)

    caption = "<b>ᴛᴏᴘ 10 ɢʀᴏᴜᴘs</b>\n\n"
    for i, g in enumerate(groups, 1):
        caption += f"{i}. <b>{html.escape(g['group_name'])}</b> ➾ <b>{g['count']}</b>\n"

    await edit_rank(cq, caption)

# ─── MTOP (COINS) ───────────────────────────────────
@app.on_callback_query(filters.regex("^mtop$"))
async def mtop_cb(_, cq):
    await asyncio.sleep(0.5)
    users = await user_collection.find().sort("coins", -1).limit(10).to_list(10)

    caption = "<b>ᴍᴛᴏᴘ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>\n\n"
    for i, u in enumerate(users, 1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','Unknown'))}</b></a>"
            f" ➾ 💸 <b>{u.get('coins',0)}</b>\n"
        )

    await edit_rank(cq, caption)

# ─── TOKENS ─────────────────────────────────────────
@app.on_callback_query(filters.regex("^tokens$"))
async def tokens_cb(_, cq):
    await asyncio.sleep(0.5)
    users = await user_collection.find().sort("tokens", -1).limit(10).to_list(10)

    caption = "<b>ᴛᴏᴋᴇɴs ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ</b>\n\n"
    for i, u in enumerate(users, 1):
        caption += (
            f"{i}. <a href='tg://user?id={u['id']}'>"
            f"<b>{html.escape(u.get('first_name','Unknown'))}</b></a>"
            f" ➾ 🪙 <b>{u.get('tokens',0)}</b>\n"
        )

    await edit_rank(cq, caption)
