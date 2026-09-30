# ==========================================================
#  PREMIUM HUB - Telegram Bot (Short ID System)
#  Bot: @Direct12_bot
# ==========================================================
import os
import re
import json
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)

# ==========================================================
#  ⚙️ তোমার তথ্য (এখানে বসানো আছে)
# ==========================================================
BOT_TOKEN = "8960530766:AAGlXoTG82mtW7AIo8AvA6dEw9T9R0CdPKY"
ADMIN_ID = 6891217464
BOT_USERNAME = "Direct12_bot"
DB_FILE = "videos.json"

# ==========================================================
#  💾 ডাটাবেজ
# ==========================================================
def load_db():
    if not os.path.exists(DB_FILE):
        return {"next_id": 1, "videos": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_video(file_id, title):
    db = load_db()
    vid = str(db["next_id"])
    db["videos"][vid] = {"file_id": file_id, "title": title}
    db["next_id"] += 1
    save_db(db)
    return vid

def get_video(vid):
    db = load_db()
    return db["videos"].get(str(vid))

# ==========================================================
#  🌐 Flask (24/7 লাইভ রাখার জন্য)
# ==========================================================
app = Flask('')

@app.route('/')
def home():
    return "✅ Premium Hub Bot is Running"

@app.route('/health')
def health():
    return "alive", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================================
#  ⏱️ ১৫ মিনিট পর ভিডিও ডিলিট
# ==========================================================
async def delete_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(
            chat_id=job.data["chat_id"],
            message_id=job.data["message_id"]
        )
        print(f"✅ Deleted: {job.data['message_id']}")
    except Exception as e:
        print(f"❌ Delete error: {e}")

# ==========================================================
#  🚀 /start
# ==========================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "👋 *Premium Hub এ স্বাগতম!*\n\n"
            "🎬 ভিডিও পেতে আমাদের ওয়েবসাইটের *Download* বাটনে ক্লিক করুন।",
            parse_mode="Markdown"
        )
        return

    video = get_video(args[0])
    if not video:
        await update.message.reply_text("❌ ভিডিওটি পাওয়া যায়নি।")
        return

    try:
        sent = await context.bot.send_video(
            chat_id=chat_id,
            video=video["file_id"],
            caption=f"🍿 *{video['title']}*\n\n"
                    f"⚠️ এই ভিডিওটি *১৫ মিনিট পর* অটো ডিলিট হবে।",
            parse_mode="Markdown"
        )
        context.job_queue.run_once(
            delete_job, when=900,
            data={"chat_id": chat_id, "message_id": sent.message_id}
        )
    except Exception as e:
        await update.message.reply_text("❌ ভিডিও পাঠানো যায়নি।")
        print(f"Send error: {e}")

# ==========================================================
#  📥 Admin: Video Upload → Short ID
# ==========================================================
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    # শুধু admin video পাঠাতে পারবে
    if update.effective_user.id != ADMIN_ID:
        await message.reply_text("❌ তুমি admin নও।")
        return

    file_id = None
    if message.video:
        file_id = message.video.file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('video/'):
        file_id = message.document.file_id
    elif message.animation:
        file_id = message.animation.file_id

    if file_id:
        title = message.caption or f"Video {load_db()['next_id']}"
        short_id = add_video(file_id, title)
        link = f"https://t.me/{BOT_USERNAME}?start={short_id}"

        await message.reply_text(
            f"✅ *ভিডিও সেভ হয়েছে!*\n\n"
            f"🆔 *Short ID:* `{short_id}`\n"
            f"📝 *Title:* {title}\n\n"
            f"🔗 *Download লিংক (ওয়েবে বসাও):*\n"
            f"`{link}`",
            parse_mode="Markdown"
        )

# ==========================================================
#  📋 /list — সব ভিডিও দেখতে
# ==========================================================
async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    db = load_db()
    if not db["videos"]:
        await update.message.reply_text("কোনো ভিডিও নেই।")
        return
    text = "📚 *সব ভিডিও:*\n\n"
    for vid, v in db["videos"].items():
        text += f"*#{vid}* — {v['title']}\n`https://t.me/{BOT_USERNAME}?start={vid}`\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ==========================================================
#  🗑️ /del <id> — ভিডিও ডিলিট
# ==========================================================
async def delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("ব্যবহার: `/del 1`", parse_mode="Markdown")
        return
    vid = context.args[0]
    db = load_db()
    if vid in db["videos"]:
        del db["videos"][vid]
        save_db(db)
        await update.message.reply_text(f"🗑️ ভিডিও #{vid} ডিলিট হয়েছে।")
    else:
        await update.message.reply_text("❌ এই ID তে কোনো ভিডিও নেই।")

# ==========================================================
#  🏁 Main
# ==========================================================
def main():
    Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_videos))
    application.add_handler(CommandHandler("del", delete_video))
    application.add_handler(MessageHandler(
        filters.VIDEO | filters.Document.VIDEO | filters.ANIMATION,
        handle_video
    ))

    print("🤖 Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
