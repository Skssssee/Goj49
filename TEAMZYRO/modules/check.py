from TEAMZYRO import app, collection as character_collection, user_collection
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ─────────────────────────────
# /check command
# ─────────────────────────────

@app.on_message(filters.command("check"))
async def check_character(_, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "Please provide a Character ID:\n`/check <character_id>`"
        )

    character_id = message.command[1]

    # Try both string & int (DB safe)
    character = await character_collection.find_one(
        {"id": character_id}
    ) or await character_collection.find_one(
        {"id": int(character_id)} if character_id.isdigit() else {}
    )

    if not character:
        return await message.reply_text("❌ Character not found.")

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("👥 Who Have It", callback_data=f"whohaveit_{character_id}")]]
    )

    text = (
        f"🌟 **Character Info**\n"
        f"🆔 ID: `{character.get('id')}`\n"
        f"📛 Name: {character.get('name','Unknown')}\n"
        f"📺 Anime: {character.get('anime','Unknown')}\n"
        f"💎 Rarity: {character.get('rarity','Unknown')}\n"
    )

    if character.get("vid_url"):
        await message.reply_video(
            character["vid_url"],
            caption=text,
            reply_markup=keyboard
        )
    else:
        await message.reply_photo(
            character.get("img_url"),
            caption=text,
            reply_markup=keyboard
        )


# ─────────────────────────────
# WHO HAVE IT CALLBACK
# ─────────────────────────────

@app.on_callback_query(filters.regex(r"^whohaveit_"))
async def who_have_it(_, callback_query):
    character_id = callback_query.data.split("_", 1)[1]

    # Fetch users having characters array
    users = await user_collection.find(
        {"characters": {"$exists": True, "$ne": []}}
    ).to_list(length=20)

    owners = []

    for user in users:
        count = 0
        for char in user.get("characters", []):
            # NEW FORMAT (dict)
            if isinstance(char, dict):
                if str(char.get("id")) == str(character_id):
                    count += 1
            # OLD FORMAT (int)
            elif isinstance(char, int):
                if str(char) == str(character_id):
                    count += 1

        if count > 0:
            owners.append((user, count))

    if not owners:
        return await callback_query.answer(
            "❌ No one owns this character yet!",
            show_alert=True
        )

    owner_text = "**🏆 Top Users Who Own This Character:**\n\n"

    for i, (user, count) in enumerate(owners[:10], 1):
        name = user.get("first_name", "Unknown")
        owner_text += (
            f"{i}. [{name}](tg://user?id={user['id']}) — **x{count}**\n"
        )

    await callback_query.message.edit_caption(
        caption=f"{callback_query.message.caption}\n\n{owner_text}",
        reply_markup=None
    )
