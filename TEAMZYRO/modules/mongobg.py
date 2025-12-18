from pyrogram import filters
from pymongo import MongoClient
import bson
import os
from TEAMZYRO import app

# ONLY THIS USER CAN USE
OWNER_ID = 1334658171

SOURCE_URI = os.getenv("MONGO_URI")
BACKUP_URI = os.getenv("BACKUP_MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "waifu_bot")


def calc_size(docs):
    return sum(len(bson.BSON.encode(d)) for d in docs)


@app.on_message(filters.command("backupdb") & filters.user(OWNER_ID))
async def backup_db(_, message):
    try:
        await message.reply_text("⏳ Starting database backup...")

        src = MongoClient(SOURCE_URI)[DB_NAME]
        dst = MongoClient(BACKUP_URI)[DB_NAME]

        total = 0
        for col in src.list_collection_names():
            docs = list(src[col].find())
            dst[col].delete_many({})
            if docs:
                dst[col].insert_many(docs)
                total += calc_size(docs)

        await message.reply_text(
            f"✅ Backup completed!\n📦 Size: `{total/1024:.2f} KB`"
        )

    except Exception as e:
        await message.reply_text(f"❌ Backup failed:\n`{e}`")


@app.on_message(filters.command("restoredb") & filters.user(OWNER_ID))
async def restore_db(_, message):
    try:
        await message.reply_text("⏳ Restoring database...")

        src = MongoClient(BACKUP_URI)[DB_NAME]
        dst = MongoClient(SOURCE_URI)[DB_NAME]

        for col in src.list_collection_names():
            docs = list(src[col].find())
            dst[col].delete_many({})
            if docs:
                dst[col].insert_many(docs)

        await message.reply_text("✅ Restore completed!")

    except Exception as e:
        await message.reply_text(f"❌ Restore failed:\n`{e}`")
