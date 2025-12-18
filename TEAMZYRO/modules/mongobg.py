from pyrogram import filters
from pymongo import MongoClient
import bson
from TEAMZYRO import app

# ─────────────────────────────
# UTILS
# ─────────────────────────────

def collection_size_mb(docs):
    size = sum(len(bson.BSON.encode(doc)) for doc in docs)
    return round(size / (1024 * 1024), 2)


def connect(uri):
    return MongoClient(uri, serverSelectionTimeoutMS=5000)


# ─────────────────────────────
# /mongobackup
# ─────────────────────────────
# Usage:
# /mongobackup SOURCE_URI BACKUP_URI DB_NAME
# ─────────────────────────────

@app.on_message(filters.command("mongobackup") & filters.private)
async def mongo_backup(_, message):
    args = message.text.split()

    if len(args) != 4:
        return await message.reply_text(
            "❌ Usage:\n"
            "`/mongobackup SOURCE_MONGO_URI BACKUP_MONGO_URI DB_NAME`"
        )

    source_uri, backup_uri, db_name = args[1], args[2], args[3]

    try:
        await message.reply_text("🔌 Connecting to databases...")

        src = connect(source_uri)
        bak = connect(backup_uri)

        src_db = src[db_name]
        bak_db = bak[db_name]

        total = 0

        for col_name in src_db.list_collection_names():
            src_col = src_db[col_name]
            bak_col = bak_db[col_name]

            docs = list(src_col.find())
            bak_col.delete_many({})

            if docs:
                bak_col.insert_many(docs)
                size = collection_size_mb(docs)
                total += size

                await message.reply_text(
                    f"✅ `{col_name}` backed up\n"
                    f"📦 Size: `{size} MB`"
                )
            else:
                await message.reply_text(f"⚠️ `{col_name}` empty, skipped")

        await message.reply_text(
            f"🎉 **BACKUP COMPLETE**\n\n"
            f"📂 Database: `{db_name}`\n"
            f"💾 Total Size: `{total} MB`"
        )

    except Exception as e:
        await message.reply_text(f"❌ Backup failed:\n`{e}`")


# ─────────────────────────────
# /mongorestore
# ─────────────────────────────
# Usage:
# /mongorestore BACKUP_URI ORIGINAL_URI DB_NAME
# ─────────────────────────────

@app.on_message(filters.command("mongorestore") & filters.private)
async def mongo_restore(_, message):
    args = message.text.split()

    if len(args) != 4:
        return await message.reply_text(
            "❌ Usage:\n"
            "`/mongorestore BACKUP_MONGO_URI ORIGINAL_MONGO_URI DB_NAME`"
        )

    backup_uri, original_uri, db_name = args[1], args[2], args[3]

    try:
        await message.reply_text("🔄 Restoring database...")

        bak = connect(backup_uri)
        org = connect(original_uri)

        bak_db = bak[db_name]
        org_db = org[db_name]

        for col_name in bak_db.list_collection_names():
            bak_col = bak_db[col_name]
            org_col = org_db[col_name]

            docs = list(bak_col.find())
            org_col.delete_many({})

            if docs:
                org_col.insert_many(docs)
                await message.reply_text(f"♻️ Restored `{col_name}`")
            else:
                await message.reply_text(f"⚠️ `{col_name}` empty, skipped")

        await message.reply_text(
            f"✅ **RESTORE COMPLETE**\n\n"
            f"📂 Database: `{db_name}`"
        )

    except Exception as e:
        await message.reply_text(f"❌ Restore failed:\n`{e}`")
