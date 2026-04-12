import os
import json
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8783176299:AAHgfs_Kk2vpBRdLHQ4XLPcjGIvJmcjQQYw"
OWNER_ID = None  # Will be set on first /start

# ─────────────────────────────────────────────
#  Helper: get Telegram CDN file URL
# ─────────────────────────────────────────────
async def get_file_url(bot, file_id: str) -> str:
    file = await bot.get_file(file_id)
    return file.file_path  # This is the full CDN URL


# ─────────────────────────────────────────────
#  Handle /start — register owner
# ─────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global OWNER_ID
    OWNER_ID = update.effective_user.id
    await update.message.reply_text(
        f"✅ Bot active!\n"
        f"Tumhara Owner ID: `{OWNER_ID}`\n\n"
        f"Ab apne channel mein video ya PDF bhejo — main automatically JSON file bana dunga!\n\n"
        f"📌 Admin panel: `/ranaji` route pe web pe milega.",
        parse_mode="Markdown"
    )


# ─────────────────────────────────────────────
#  Handle channel posts (video / document / photo)
# ─────────────────────────────────────────────
async def handle_channel_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post or update.message
    if not msg:
        return

    bot = ctx.bot
    caption = msg.caption or msg.text or ""
    chat = msg.chat
    post_id = msg.message_id

    item = {
        "post_id": post_id,
        "channel": chat.username or str(chat.id),
        "caption": caption,
        "type": None,
        "file_id": None,
        "cdn_url": None,
        "tg_link": f"https://t.me/{chat.username}/{post_id}" if chat.username else None,
        "mime_type": None,
        "file_name": None,
        "thumb": None,
    }

    # VIDEO
    if msg.video:
        v = msg.video
        item["type"] = "video"
        item["file_id"] = v.file_id
        item["mime_type"] = v.mime_type
        item["file_name"] = v.file_name or f"video_{post_id}.mp4"
        item["duration"] = v.duration
        item["width"] = v.width
        item["height"] = v.height
        if v.thumbnail:
            try:
                item["thumb"] = await get_file_url(bot, v.thumbnail.file_id)
            except:
                pass
        try:
            item["cdn_url"] = await get_file_url(bot, v.file_id)
        except Exception as e:
            item["cdn_url"] = None
            item["error"] = f"File too large for Bot API (>20MB): {str(e)}"

    # DOCUMENT (PDF etc)
    elif msg.document:
        d = msg.document
        item["type"] = "document"
        item["file_id"] = d.file_id
        item["mime_type"] = d.mime_type
        item["file_name"] = d.file_name or f"file_{post_id}"
        if d.mime_type == "application/pdf":
            item["type"] = "pdf"
        if d.thumbnail:
            try:
                item["thumb"] = await get_file_url(bot, d.thumbnail.file_id)
            except:
                pass
        try:
            item["cdn_url"] = await get_file_url(bot, d.file_id)
        except Exception as e:
            item["cdn_url"] = None
            item["error"] = f"File too large for Bot API (>20MB): {str(e)}"

    # PHOTO
    elif msg.photo:
        p = msg.photo[-1]
        item["type"] = "photo"
        item["file_id"] = p.file_id
        try:
            item["cdn_url"] = await get_file_url(bot, p.file_id)
        except:
            pass

    else:
        return  # Ignore text-only messages

    # ── Build JSON ──
    json_str = json.dumps(item, ensure_ascii=False, indent=2)

    # ── Send JSON file to owner / sender ──
    target = update.effective_user.id if update.effective_user else OWNER_ID
    if not target:
        return

    filename = f"post_{post_id}.json"
    json_bytes = json_str.encode("utf-8")

    await bot.send_document(
        chat_id=target,
        document=json_bytes,
        filename=filename,
        caption=(
            f"✅ *New Post Captured!*\n"
            f"📌 Type: `{item['type']}`\n"
            f"🔢 Post ID: `{post_id}`\n"
            f"📝 Caption: {caption[:100] or '—'}\n\n"
            f"⬇️ Is JSON file ko Admin Panel mein upload karo:\n"
            f"`yoursite.vercel.app/ranaji`"
        ),
        parse_mode="Markdown"
    )

    # Also send a nice text summary
    cdn_status = "✅ CDN URL mili!" if item["cdn_url"] else "⚠️ File >20MB — Telegram embed use hoga"
    await bot.send_message(
        chat_id=target,
        text=(
            f"*CDN Status:* {cdn_status}\n"
            + (f"🔗 `{item['cdn_url']}`" if item["cdn_url"] else f"🔗 TG Link: {item['tg_link']}")
        ),
        parse_mode="Markdown"
    )


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    from telegram.ext import CommandHandler
    app.add_handler(CommandHandler("start", start))

    # Listen to messages sent directly to bot (forwarded from channel)
    app.add_handler(MessageHandler(
        filters.VIDEO | filters.Document.ALL | filters.PHOTO,
        handle_channel_post
    ))

    # Also listen to actual channel posts if bot is admin
    app.add_handler(MessageHandler(
        filters.UpdateType.CHANNEL_POSTS & (filters.VIDEO | filters.Document.ALL | filters.PHOTO),
        handle_channel_post
    ))

    print("🤖 Bot running... Send /start first!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
