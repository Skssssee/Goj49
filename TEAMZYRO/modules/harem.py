import math
import random
import asyncio
from html import escape
from itertools import groupby

from pyrogram import filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from TEAMZYRO import app, user_collection, collection
from TEAMZYRO.unit.zyro_rarity import rarity_map2


# ─────────────────────────────────────────────
# SAFE FETCH USER CHARACTERS
# ─────────────────────────────────────────────
async def fetch_user_characters(user_id: int):
    user = await user_collection.find_one({"id": user_id})

    if not user:
        return None, "You have not guessed any characters yet."

    characters = user.get("characters", [])

    # 🔥 HARD FIX (INT / NONE BUG)
    if not isinstance(characters, list):
        characters = []
        await user_collection.update_one(
            {"id": user_id},
            {"$set": {"characters": []}}
        )

    characters = [
        c for c in characters
        if isinstance(c, dict) and "id" in c
    ]

    if not characters:
        return None, "No valid characters found in your collection."

    return characters, None


# ─────────────────────────────────────────────
# HAREM / COLLECTION COMMAND
# ─────────────────────────────────────────────
@app.on_message(filters.command(["harem", "collection"]))
async def harem_handler(client, message: Message):
    user_id = message.from_user.id

    user = await user_collection.find_one({"id": user_id})
    filter_rarity = user.get("filter_rarity") if user else None

    msg = await display_harem(
        client,
        message,
        user_id,
        page=0,
        filter_rarity=filter_rarity,
        is_initial=True
    )

    if msg:
        await asyncio.sleep(180)
        await msg.delete()


# ─────────────────────────────────────────────
# MAIN DISPLAY FUNCTION
# ─────────────────────────────────────────────
async def display_harem(
    client,
    message: Message,
    user_id: int,
    page: int,
    filter_rarity=None,
    is_initial=False,
    callback_query=None
):
    try:
        characters, error = await fetch_user_characters(user_id)
        if error:
            return await message.reply_text(error)

        # Sort characters
        characters.sort(key=lambda x: (x.get("anime", ""), x.get("id", "")))

        # Filter by rarity
        if filter_rarity:
            characters = [
                c for c in characters
                if c.get("rarity") == filter_rarity
            ]

            if not characters:
                return await message.reply_text(
                    f"No characters found with rarity **{filter_rarity}**"
                )

        # Count duplicates safely
        characters_sorted = sorted(characters, key=lambda x: x["id"])
        char_count = {
            k: len(list(v))
            for k, v in groupby(characters_sorted, key=lambda x: x["id"])
        }

        unique_chars = list(
            {c["id"]: c for c in characters_sorted}.values()
        )

        per_page = 15
        total_pages = max(1, math.ceil(len(unique_chars) / per_page))
        page = max(0, min(page, total_pages - 1))

        # Build text
        text = (
            f"<b>{escape(message.from_user.first_name)}'s Harem</b>\n"
            f"Page {page+1}/{total_pages}\n"
        )

        if filter_rarity:
            text += f"<b>Filter:</b> {filter_rarity}\n"

        current = unique_chars[page * per_page:(page + 1) * per_page]

        for anime, chars in groupby(current, key=lambda x: x["anime"]):
            chars = list(chars)
            total_in_anime = await collection.count_documents({"anime": anime})
            text += f"\n<b>{anime} {len(chars)}/{total_in_anime}</b>\n"

            for c in chars:
                emoji = rarity_map2.get(c.get("rarity"), "")
                text += (
                    f"◈⌠{emoji}⌡ "
                    f"{c['id']} {c['name']} ×{char_count[c['id']]}\n"
                )

        # Buttons
        keyboard = [
            [
                InlineKeyboardButton(
                    "Collection",
                    switch_inline_query_current_chat=f"collection.{user_id}"
                ),
                InlineKeyboardButton(
                    "💌 AMV",
                    switch_inline_query_current_chat=f"collection.{user_id}.AMV"
                ),
            ]
        ]

        nav = []
        if page > 0:
            nav.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=f"harem:{page-1}:{user_id}:{filter_rarity or 'None'}"
                )
            )
        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=f"harem:{page+1}:{user_id}:{filter_rarity or 'None'}"
                )
            )
        if nav:
            keyboard.append(nav)

        markup = InlineKeyboardMarkup(keyboard)

        # Pick image / video
        media_char = random.choice(characters)

        # SEND
        if is_initial:
            if media_char.get("vid_url"):
                return await message.reply_video(
                    media_char["vid_url"],
                    caption=text,
                    reply_markup=markup,
                    parse_mode=enums.ParseMode.HTML
                )
            elif media_char.get("img_url"):
                return await message.reply_photo(
                    media_char["img_url"],
                    caption=text,
                    reply_markup=markup,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                return await message.reply_text(
                    text,
                    reply_markup=markup,
                    parse_mode=enums.ParseMode.HTML
                )

        # EDIT (callback)
        if media_char.get("vid_url"):
            await callback_query.message.edit_media(
                InputMediaVideo(
                    media_char["vid_url"],
                    caption=text,
                    parse_mode=enums.ParseMode.HTML
                ),
                reply_markup=markup
            )
        elif media_char.get("img_url"):
            await callback_query.message.edit_media(
                InputMediaPhoto(
                    media_char["img_url"],
                    caption=text,
                    parse_mode=enums.ParseMode.HTML
                ),
                reply_markup=markup
            )
        else:
            await callback_query.message.edit_text(
                text,
                reply_markup=markup,
                parse_mode=enums.ParseMode.HTML
            )

    except Exception as e:
        print(f"[HAREM ERROR] {e}")
        await message.reply_text("An error occurred. Please try again later.")


# ─────────────────────────────────────────────
# CALLBACK NAVIGATION
# ─────────────────────────────────────────────
@app.on_callback_query(filters.regex("^harem:"))
async def harem_callback(client, cq):
    _, page, user_id, rarity = cq.data.split(":")
    page = int(page)
    user_id = int(user_id)
    rarity = None if rarity == "None" else rarity

    if cq.from_user.id != user_id:
        return await cq.answer("Not your harem!", show_alert=True)

    await display_harem(
        client,
        cq.message,
        user_id,
        page,
        rarity,
        is_initial=False,
        callback_query=cq
    )
