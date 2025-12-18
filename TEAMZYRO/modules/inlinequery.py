import re
import time
from html import escape
from telegram import Update, InlineQueryResultPhoto, InlineQueryResultVideo
from telegram.ext import InlineQueryHandler, CallbackContext
from TEAMZYRO import application
from TEAMZYRO.unit.zyro_inline import *

# ===============================
# INLINE QUERY HANDLER
# ===============================

async def inlinequery(update: Update, context: CallbackContext):
    query = update.inline_query.query.strip()
    offset = int(update.inline_query.offset or 0)

    try:
        all_characters = []
        is_amv = False
        user = None

        # -------------------------------
        # PARSE COLLECTION QUERY
        # -------------------------------
        if query.startswith("collection."):
            # collection.USERID or collection.USERID.AMV
            parts = query.split(".")

            user_id = parts[1] if len(parts) >= 2 else None
            is_amv = len(parts) == 3 and parts[2].upper() == "AMV"

            if user_id and user_id.isdigit():
                user = await get_user_collection(user_id)
                if user:
                    all_characters = user.get("characters", [])

        # -------------------------------
        # MEDIA FILTER
        # -------------------------------
        if is_amv:
            all_characters = [
                c for c in all_characters
                if isinstance(c.get("vid_url"), str)
                and c["vid_url"].startswith("http")
            ]
        else:
            all_characters = [
                c for c in all_characters
                if isinstance(c.get("img_url"), str)
                and c["img_url"].startswith("http")
            ]

        # -------------------------------
        # PAGINATION
        # -------------------------------
        all_characters = all_characters[offset: offset + 50]
        next_offset = str(offset + 50) if len(all_characters) == 50 else None

        results = []

        # -------------------------------
        # BUILD INLINE RESULTS
        # -------------------------------
        for character in all_characters:
            if not all(k in character for k in ("id", "name", "anime", "rarity")):
                continue

            caption = (
                f"<b>{escape(character['name'])}</b>\n"
                f"🏖️ {escape(character['anime'])}\n"
                f"🔮 {escape(character['rarity'])}\n"
                f"🆔 <code>{character['id']}</code>"
            )

            # 🎥 AMV VIDEO
            if is_amv and character.get("vid_url"):
                results.append(
                    InlineQueryResultVideo(
                        id=f"vid_{character['id']}_{time.time()}",
                        video_url=character["vid_url"],
                        mime_type="video/mp4",
                        thumbnail_url=character.get("thum_url", character["vid_url"]),
                        title=character["name"],
                        caption=caption,
                        parse_mode="HTML",
                    )
                )

            # 🖼️ IMAGE
            elif not is_amv and character.get("img_url"):
                results.append(
                    InlineQueryResultPhoto(
                        id=f"img_{character['id']}_{time.time()}",
                        photo_url=character["img_url"],
                        thumbnail_url=character["img_url"],  # IMPORTANT
                        caption=caption,
                        parse_mode="HTML",
                    )
                )

        await update.inline_query.answer(
            results,
            next_offset=next_offset,
            cache_time=1
        )

    except Exception as e:
        print("INLINE ERROR:", e)
        await update.inline_query.answer([], cache_time=1)


# ===============================
# REGISTER HANDLER
# ===============================
application.add_handler(InlineQueryHandler(inlinequery, block=False))
