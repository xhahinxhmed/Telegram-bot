# ==========================================
# PREMIUM HUB - Telegram Bot + Flask 24/7
# ==========================================
import os
import re
import json
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)

# ==========================================
# ⚙️ CONFIGURATION (শুধু এই ২টা লাইন পরিবর্তন করো)
# ==========================================
BOT_TOKEN = "8960530766:AAGlXoTG82mtW7AIo8AvA6dEw9T9R0CdPKY"   # <-- নতুন token বসাও
ADMIN_ID = "6891217464"                                                    # <-- তোমার Telegram numeric ID বসাও
DB_FILE = "videos.json"

# ==========================================
# 💾 DATABASE (Short ID ↔ File ID)
# ==========================================
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

# ==========================================
# 🌐 FLASK (24/7 Alive রাখার জন্য)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "✅ Premium Hub Bot is Running 24/7"

@app.route('/health')
def health():
    return "alive", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ==========================================
# ⏱️ ১৫ মিনিট পর ভিডিও ডিলিট
# ==========================================
async def delete_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(
            chat_id=job.data["chat_id"],
            message_id=job.data["message_id"]
        )
        print(f"✅ Video deleted after 15 min: {job.data['message_id']}")
    except Exception as e:
        print(f"❌ Delete error: {e}")

# ==========================================
# 🚀 /start COMMAND (User এখান থেকে আসে)
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "👋 **Premium Hub এ স্বাগতম!**\n\n"
            "🎬 ভিডিও ডাউনলোড করতে আমাদের ওয়েবসাইটে যান এবং "
            "**Download** বাটনে ক্লিক করুন।",
            parse_mode="Markdown"
        )
        return

    short_id = args[0]
    video = get_video(short_id)

    if not video:
        await update.message.reply_text(
            "❌ **ভিডিওটি পাওয়া যায়নি!**\n\n"
            "সম্ভবত লিংকটি ভুল বা ভিডিওটি ডিলিট হয়ে গেছে।",
            parse_mode="Markdown"
        )
        return

    try:
        sent = await context.bot.send_video(
            chat_id=chat_id,
            video=video["file_id"],
            caption=f"🍿 **{video['title']}**\n\n"
                    f"⚠️ এই ভিডিওটি **১৫ মিনিট পর** স্বয়ংক্রিয়ভাবে মুছে যাবে।\n"
                    f"⏳ দয়া করে এর মধ্যে দেখে নিন বা সেভ করে নিন।",
            parse_mode="Markdown"
        )
        # Job queue দিয়ে ১৫ মিনিট (৯০০ সেকেন্ড) পর delete
        context.job_queue.run_once(
            delete_job,
            when=900,
            data={"chat_id": chat_id, "message_id": sent.message_id},
            name=f"del_{chat_id}_{sent.message_id}"
        )
    except Exception as e:
        await update.message.reply_text(
            "❌ দুঃখিত! ভিডিওটি পাঠানো যায়নি। file_id টি সঠিক নয়।"
        )
        print(f"Send error: {e}")

# ==========================================
# 📥 ADMIN: ভিডিও আপলোড করলে Short ID + Link দেয়
# ==========================================
async def catch_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    # শুধু admin video পাঠাতে পারবে (ADMIN_ID সেট থাকলে)
    if ADMIN_ID and update.effective_user.id != ADMIN_ID:
        if message.video or message.document or message.animation:
            await message.reply_text("❌ তুমি admin নও।")
        return

    file_id = None

    # সরাসরি video / document / animation
    if message.video:
        file_id = message.video.file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('video/'):
        file_id = message.document.file_id
    elif message.animation:
        file_id = message.animation.file_id

    # চ্যানেল link থেকে file_id বের করা
    elif message.text and "t.me/" in message.text:
        link_parts = re.findall(r't\.me/(?:c/)?([^/]+)/(\d+)', message.text)
        if link_parts:
            channel_peer, msg_id = link_parts[0]
            message_id = int(msg_id)
            chat_target = int(f"-100{channel_peer}") if channel_peer.isdigit() else f"@{channel_peer}"
            try:
                target_msg = await context.bot.forward_message(
                    chat_id=message.chat_id,
                    from_chat_id=chat_target,
                    message_id=message_id
                )
                if target_msg.video:
                    file_id = target_msg.video.file_id
                elif target_msg.document:
                    file_id = target_msg.document.file_id
                elif target_msg.animation:
                    file_id = target_msg.animation.file_id

                await context.bot.delete_message(
                    chat_id=message.chat_id,
                    message_id=target_msg.message_id
                )
            except Exception as e:
                await message.reply_text(
                    "❌ চ্যানেল থেকে ফাইল রিড করা যায়নি। "
                    "নিশ্চিত হোন বটটি চ্যানেলের admin কিনা।"
                )
                print(e)
                return

    # file_id পেলে short id বানিয়ে সেভ + web link রিপ্লাই
    if file_id:
        title = message.caption or f"Video {load_db()['next_id']}"
        short_id = add_video(file_id, title)
        bot_username = context.bot.username
        final_link = f"https://t.me/{bot_username}?start={short_id}"

        await message.reply_text(
            f"✅ **ভিডিও সেভ হয়েছে!**\n\n"
            f"🆔 **Short ID:** `{short_id}`\n"
            f"📝 **Title:** {title}\n\n"
            f"🔗 **ওয়েবসাইটের Download বাটনে এই লিংক বসাও:**\n"
            f"`{final_link}`\n\n"
            f"📋 **File ID (ব্যাকআপ):**\n`{file_id}`",
            parse_mode="Markdown"
        )

# ==========================================
# 📋 /list — সব ভিডিও দেখতে
# ==========================================
async def list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_ID and update.effective_user.id != ADMIN_ID:
        return
    db = load_db()
    if not db["videos"]:
        await update.message.reply_text("কোনো ভিডিও সেভ করা নেই।")
        return
    bot_username = context.bot.username
    text = "📚 **সব ভিডিও লিস্ট:**\n\n"
    for vid, v in db["videos"].items():
        text += f"**#{vid}** — {v['title']}\n`https://t.me/{bot_username}?start={vid}`\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ==========================================
# 🗑️ /del <id> — ভিডিও ডিলিট
# ==========================================
async def delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_ID and update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("ব্যবহার: `/del 5`", parse_mode="Markdown")
        return
    vid = context.args[0]
    db = load_db()
    if vid in db["videos"]:
        del db["videos"][vid]
        save_db(db)
        await update.message.reply_text(f"🗑️ ভিডিও #{vid} ডিলিট হয়েছে।")
    else:
        await update.message.reply_text("❌ এই ID তে কোনো ভিডিও নেই।")

# ==========================================
# 🏁 MAIN
# ==========================================
def main():
    Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_videos))
    application.add_handler(CommandHandler("del", delete_video))
    application.add_handler(MessageHandler(filters.ALL, catch_everything))

    print("🤖 Premium Hub Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
