from pyrogram import filters
from pymongo import MongoClient
import bson
import os
from TEAMZYRO import app

OWNER_ID = 1334658171

SOURCE_URI = os.getenv("MONGO_URI")
BACKUP_URI = os.getenv("BACKUP_MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "waifu_bot")


def calc_size(docs):
    return sum(len(bson.BSON.encode(d)) for d in docs)


def check_env():
    return SOURCE_URI and BACKUP_URI and DB_NAME


# ───────── BACKUP (ALL CHATS) ─────────
@app.on_message(
    filters.command("backupdb") &
    filters.user(OWNER_ID)
)
async def backup_db(_, message):
    if not check_env():
        return await message.reply_text("❌ ENV variables missing")

    try:
        await message.reply_text("⏳ Starting database BACKUP...")

        src_db = MongoClient(SOURCE_URI)[DB_NAME]
        dst_db = MongoClient(BACKUP_URI)[DB_NAME]

        total_docs = 0
        total_bytes = 0

        for col in src_db.list_collection_names():
            docs = list(src_db[col].find())
            dst_db[col].delete_many({})
            if docs:
                dst_db[col].insert_many(docs)
                total_docs += len(docs)
                total_bytes += calc_size(docs)

        await message.reply_text(
            "✅ BACKUP COMPLETED\n\n"
            f"📂 DB: `{DB_NAME}`\n"
            f"📄 Docs: `{total_docs}`\n"
            f"💾 Size: `{total_bytes/1024:.2f} KB`"
        )

    except Exception as e:
        await message.reply_text(f"❌ Backup failed:\n`{e}`")


# ───────── RESTORE (ALL CHATS) ─────────
@app.on_message(
    filters.command("restoredb") &
    filters.user(OWNER_ID)
)
async def restore_db(_, message):
    if not check_env():
        return await message.reply_text("❌ ENV variables missing")

    try:
        await message.reply_text("⚠️ Restoring database...")

        src_db = MongoClient(BACKUP_URI)[DB_NAME]
        dst_db = MongoClient(SOURCE_URI)[DB_NAME]

        total_docs = 0

        for col in src_db.list_collection_names():
            docs = list(src_db[col].find())
            dst_db[col].delete_many({})
            if docs:
                dst_db[col].insert_many(docs)
                total_docs += len(docs)

        await message.reply_text(
            "✅ RESTORE COMPLETED\n\n"
            f"📄 Documents restored: `{total_docs}`"
        )

    except Exception as e:
        await message.reply_text(f"❌ Restore failed:\n`{e}`")l
