import asyncio
from pyrogram import filters
from pyrogram.errors import FloodWait, PeerIdInvalid, ChatWriteForbidden
from TEAMZYRO import app, user_collection, top_global_groups_collection, require_power


@app.on_message(filters.command("bcast"))
@require_power("bcast")
async def broadcast(_, message):
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a message to broadcast.")

    src = message.reply_to_message
    status = await message.reply_text("📢 Broadcast started...")

    user_ok = 0
    group_ok = 0
    failed = 0
    sent = 0


    async def send(chat_id: int, is_group=False):
        nonlocal failed, sent
        try:
            await src.forward(chat_id)
            sent += 1
            return True

        except FloodWait as e:
            await asyncio.sleep(e.value)
            return await send(chat_id, is_group)

        except (PeerIdInvalid, ChatWriteForbidden):
            failed += 1
            # auto-remove dead groups
            if is_group:
                await top_global_groups_collection.delete_one({"group_id": chat_id})
            return False

        except Exception as e:
            print(f"[BCAST ERROR] {chat_id}: {e}")
            failed += 1
            return False

        finally:
            if sent % 7 == 0:
                await asyncio.sleep(2)


    # ───────── USERS ─────────
    async for user in user_collection.find({}, {"id": 1}):
        uid = user.get("id")
        if not isinstance(uid, int):
            continue

        if await send(uid):
            user_ok += 1

        if user_ok % 100 == 0:
            await status.edit_text(
                f"📢 Broadcasting...\n\n"
                f"👤 Users: {user_ok}\n"
                f"👥 Groups: {group_ok}\n"
                f"❌ Failed: {failed}"
            )


    # ───────── GROUPS ─────────
    seen = set()

    async for grp in top_global_groups_collection.find({}, {"group_id": 1}):
        gid = grp.get("group_id")

        # HARD VALIDATION
        if not isinstance(gid, int):
            await top_global_groups_collection.delete_one({"group_id": gid})
            continue

        if not str(gid).startswith("-100"):
            await top_global_groups_collection.delete_one({"group_id": gid})
            continue

        if gid in seen:
            continue

        seen.add(gid)

        if await send(gid, is_group=True):
            group_ok += 1

        if group_ok % 50 == 0:
            await status.edit_text(
                f"📢 Broadcasting...\n\n"
                f"👤 Users: {user_ok}\n"
                f"👥 Groups: {group_ok}\n"
                f"❌ Failed: {failed}"
            )


    await status.edit_text(
        f"✅ Broadcast Completed!\n\n"
        f"👤 Users sent: {user_ok}\n"
        f"👥 Groups sent: {group_ok}\n"
        f"❌ Failed: {failed}"
    )
