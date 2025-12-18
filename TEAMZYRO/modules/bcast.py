import asyncio
from pyrogram import filters
from pyrogram.errors import PeerIdInvalid, FloodWait, ChatWriteForbidden
from TEAMZYRO import app, user_collection, top_global_groups_collection, require_power


@app.on_message(filters.command("bcast"))
@require_power("bcast")
async def broadcast(_, message):
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a message to broadcast.")

    source_msg = message.reply_to_message
    progress = await message.reply_text("📢 Broadcast started...")

    user_success = 0
    group_success = 0
    failed = 0
    sent_count = 0

    # ─────────────────────────────
    # SAFE SEND FUNCTION
    # ─────────────────────────────
    async def send_to(chat_id):
        nonlocal failed, sent_count
        try:
            await source_msg.copy(chat_id)
            sent_count += 1
            return True
        except FloodWait as e:
            await asyncio.sleep(e.value)
            return await send_to(chat_id)
        except (PeerIdInvalid, ChatWriteForbidden):
            failed += 1
            return False
        except Exception as e:
            print(f"[BCAST ERROR] {chat_id}: {e}")
            failed += 1
            return False
        finally:
            if sent_count % 7 == 0:
                await asyncio.sleep(2)

    # ─────────────────────────────
    # BROADCAST TO USERS
    # ─────────────────────────────
    async for user in user_collection.find({}, {"id": 1}):
        uid = user.get("id")
        if not uid:
            continue

        ok = await send_to(uid)
        if ok:
            user_success += 1

        if user_success % 100 == 0:
            await progress.edit_text(
                f"📢 Broadcasting...\n\n"
                f"👤 Users: {user_success}\n"
                f"👥 Groups: {group_success}\n"
                f"❌ Failed: {failed}"
            )

    # ─────────────────────────────
    # BROADCAST TO GROUPS
    # ─────────────────────────────
    group_ids = set()

    async for grp in top_global_groups_collection.find({}, {"group_id": 1}):
        gid = grp.get("group_id")
        if not gid or gid in group_ids:
            continue

        group_ids.add(gid)
        ok = await send_to(gid)
        if ok:
            group_success += 1

        if group_success % 50 == 0:
            await progress.edit_text(
                f"📢 Broadcasting...\n\n"
                f"👤 Users: {user_success}\n"
                f"👥 Groups: {group_success}\n"
                f"❌ Failed: {failed}"
            )

    # ─────────────────────────────
    # FINAL REPORT
    # ─────────────────────────────
    await progress.edit_text(
        f"✅ Broadcast Completed!\n\n"
        f"👤 Users sent: {user_success}\n"
        f"👥 Groups sent: {group_success}\n"
        f"❌ Failed: {failed}"
    )
