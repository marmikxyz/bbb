import os
import re
import json
import time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8756162788:AAEZV09m8X1napx-JKiK6FPa2fTrZjo0qWY")

# In-memory draft store: { user_id: {title, category, duration, questions: [...]} }
DRAFTS = {}

QUESTION_BLOCK_RE = re.compile(
    r"Q:\s*(?P<q>.+?)\s*\n"
    r"A\)\s*(?P<a>.+?)\s*\n"
    r"B\)\s*(?P<b>.+?)\s*\n"
    r"C\)\s*(?P<c>.+?)\s*\n"
    r"D\)\s*(?P<d>.+?)\s*\n"
    r"Correct:\s*(?P<correct>[ABCDabcd])\s*"
    r"(?:\n?Explanation:\s*(?P<explanation>.*))?",
    re.MULTILINE,
)

HELP_TEXT = (
    "*Quiz Bot — kaise use kare*\n\n"
    "1️⃣ `/newquiz Title | Category | Duration(min)`\n"
    "   e.g. `/newquiz SSC GK Mock 1 | General Knowledge | 15`\n\n"
    "2️⃣ Fir har question is format mein bhejo (ek message mein multiple bhi chalega, "
    "blank line se separate karo):\n\n"
    "```\n"
    "Q: Capital of France kya hai?\n"
    "A) Paris\n"
    "B) London\n"
    "C) Berlin\n"
    "D) Madrid\n"
    "Correct: A\n"
    "Explanation: Paris France ki capital hai.\n"
    "```\n"
    "_(Explanation optional hai)_\n\n"
    "3️⃣ `/status` — kitne questions add hue dekho\n"
    "4️⃣ `/removelast` — last question hataye\n"
    "5️⃣ `/done` — quiz finalize karo, JSON file milegi\n"
    "6️⃣ Us JSON ko Admin Panel (`/admin` route) pe **Import** karo aur Publish dabao\n\n"
    "`/cancel` — draft discard karo"
)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


async def newquiz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    raw = update.message.text.partition(" ")[2].strip()
    if not raw or "|" not in raw:
        await update.message.reply_text(
            "Format: `/newquiz Title | Category | Duration(min)`\n"
            "e.g. `/newquiz SSC GK Mock 1 | General Knowledge | 15`",
            parse_mode="Markdown",
        )
        return

    parts = [p.strip() for p in raw.split("|")]
    title = parts[0] if len(parts) > 0 and parts[0] else "Untitled Quiz"
    category = parts[1] if len(parts) > 1 and parts[1] else "General"
    try:
        duration = int(parts[2]) if len(parts) > 2 and parts[2] else 10
    except ValueError:
        duration = 10

    DRAFTS[user_id] = {
        "title": title,
        "category": category,
        "duration_minutes": duration,
        "questions": [],
    }

    await update.message.reply_text(
        f"✅ Naya quiz shuru hua: *{title}*\n"
        f"📂 Category: {category}\n"
        f"⏱️ Duration: {duration} min\n\n"
        f"Ab questions bhejo (format ke liye /start dekho).",
        parse_mode="Markdown",
    )


async def status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    draft = DRAFTS.get(user_id)
    if not draft:
        await update.message.reply_text("Koi active draft nahi hai. `/newquiz` se shuru karo.")
        return
    await update.message.reply_text(
        f"📋 *{draft['title']}* — {len(draft['questions'])} question(s) added.",
        parse_mode="Markdown",
    )


async def removelast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    draft = DRAFTS.get(user_id)
    if not draft or not draft["questions"]:
        await update.message.reply_text("Hataane ke liye koi question nahi hai.")
        return
    removed = draft["questions"].pop()
    await update.message.reply_text(f"🗑️ Hataya gaya: {removed['text'][:80]}")


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if DRAFTS.pop(user_id, None):
        await update.message.reply_text("❌ Draft discard ho gaya.")
    else:
        await update.message.reply_text("Koi active draft nahi tha.")


async def done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    draft = DRAFTS.get(user_id)
    if not draft or not draft["questions"]:
        await update.message.reply_text(
            "Quiz khaali hai — pehle kuch questions add karo."
        )
        return

    slug_title = re.sub(r"[^a-z0-9]+", "-", draft["title"].lower()).strip("-")
    quiz = {
        "id": f"{slug_title}-{int(time.time())}",
        "title": draft["title"],
        "category": draft["category"],
        "duration_minutes": draft["duration_minutes"],
        "questions": draft["questions"],
    }

    json_bytes = json.dumps(quiz, ensure_ascii=False, indent=2).encode("utf-8")
    filename = f"{quiz['id']}.json"

    await ctx.bot.send_document(
        chat_id=update.effective_chat.id,
        document=json_bytes,
        filename=filename,
        caption=(
            f"✅ *Quiz Ready!*\n"
            f"📌 {quiz['title']} ({len(quiz['questions'])} questions)\n\n"
            f"Is file ko Admin Panel ke *Import* tab mein daalo, review karo, "
            f"phir *Publish* dabao."
        ),
        parse_mode="Markdown",
    )

    DRAFTS.pop(user_id, None)


async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    draft = DRAFTS.get(user_id)
    if not draft:
        await update.message.reply_text(
            "Pehle `/newquiz Title | Category | Duration(min)` se shuru karo."
        )
        return

    text = update.message.text.strip()
    blocks = re.split(r"\n\s*\n", text)

    added = 0
    failed = 0
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        m = QUESTION_BLOCK_RE.search(block)
        if not m:
            failed += 1
            continue

        correct_letter = m.group("correct").upper()
        correct_index = "ABCD".index(correct_letter)

        draft["questions"].append(
            {
                "text": m.group("q").strip(),
                "options": [
                    m.group("a").strip(),
                    m.group("b").strip(),
                    m.group("c").strip(),
                    m.group("d").strip(),
                ],
                "correct": correct_index,
                "explanation": (m.group("explanation") or "").strip(),
            }
        )
        added += 1

    if added:
        await update.message.reply_text(
            f"✅ {added} question(s) add hue. Total: {len(draft['questions'])}"
            + (f"\n⚠️ {failed} block(s) parse nahi hue — format check karo." if failed else "")
        )
    else:
        await update.message.reply_text(
            "⚠️ Format samajh nahi aaya. `/start` bhejke sahi format dekho."
        )


def main():
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise SystemExit(
            "Set your bot token first: export BOT_TOKEN=... (get one from @BotFather)"
        )

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newquiz", newquiz))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("removelast", removelast))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Quiz bot running... Send /start on Telegram.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
