import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = "YOUR_BOT_TOKEN"

OWNER_ID = None


# --------------------------------------------------
# /start
# --------------------------------------------------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    global OWNER_ID

    OWNER_ID = update.effective_user.id

    await update.message.reply_text(
        "✅ Quiz Bot Activated!\n\n"
        "Send a quiz JSON file.\n\n"
        "I'll verify it and send it back ready for your website."
    )


# --------------------------------------------------
# Validate Quiz
# --------------------------------------------------
def validate_quiz(data):

    if not isinstance(data, dict):
        return False, "Root must be object."

    required = [
        "title",
        "category",
        "duration",
        "negative_marking",
        "questions",
    ]

    for key in required:
        if key not in data:
            return False, f"Missing field: {key}"

    if not isinstance(data["questions"], list):
        return False, "questions must be list."

    if len(data["questions"]) == 0:
        return False, "No questions found."

    for i, q in enumerate(data["questions"], start=1):

        if "question" not in q:
            return False, f"Question {i} missing question."

        if "options" not in q:
            return False, f"Question {i} missing options."

        if "answer" not in q:
            return False, f"Question {i} missing answer."

        if len(q["options"]) != 4:
            return False, f"Question {i} must have 4 options."

    return True, "OK"


# --------------------------------------------------
# Receive Quiz JSON
# --------------------------------------------------
async def receive_quiz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):

    global OWNER_ID

    msg = update.message

    if msg is None:
        return

    if not msg.document:
        return

    document = msg.document

    if not document.file_name.lower().endswith(".json"):
        await msg.reply_text("❌ Please send a JSON file.")
        return

    file = await document.get_file()

    raw = await file.download_as_bytearray()

    try:
        quiz = json.loads(raw.decode("utf-8"))
    except Exception:
        await msg.reply_text("❌ Invalid JSON.")
        return

    ok, reason = validate_quiz(quiz)

    if not ok:
        await msg.reply_text(f"❌ Validation Failed\n\n{reason}")
        return

    quiz["total_questions"] = len(quiz["questions"])

    output = json.dumps(
        quiz,
        indent=2,
        ensure_ascii=False,
    )

    filename = (
        quiz["title"]
        .replace(" ", "_")
        .replace("/", "_")
        + ".json"
    )

    target = OWNER_ID or update.effective_user.id

    await ctx.bot.send_document(
        chat_id=target,
        document=output.encode(),
        filename=filename,
        caption=(
            "✅ Quiz Verified Successfully\n\n"
            f"Title : {quiz['title']}\n"
            f"Questions : {len(quiz['questions'])}\n\n"
            "Upload this JSON in your Admin Panel."
        ),
    )


# --------------------------------------------------
# Main
# --------------------------------------------------
def main():

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(
            filters.Document.ALL,
            receive_quiz,
        )
    )

    print("Quiz Bot Running...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
