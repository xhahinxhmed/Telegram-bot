import asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8854706838:AAGGuJwBt--Dyh12BKyBJ7YljP_IpMvo2DM"  

app = Flask('')

@app.route('/')
def home(): 
    return "Bot is Running 24/7!"

def run_flask(): 
    app.run(host='0.0.0.0', port=8080)

async def delete_message_after_delay(chat_id, message_id, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(900)  
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"Message {message_id} deleted successfully.")
    except Exception as e:
        print(f"Error deleting message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args  

    if args:
        file_id = args if isinstance(args, list) else args
        try:
            sent_message = await context.bot.send_video(
                chat_id=chat_id, 
                video=file_id, 
                caption="🍿 আপনার কাঙ্ক্ষিত ভিডিওটি এখানে! এটি ১৫ মিনিট পর স্বয়ংক্রিয়ভাবে ডিলিট হয়ে যাবে।"
            )
            asyncio.create_task(delete_message_after_delay(chat_id, sent_message.message_id, context))
        except Exception as e:
            await update.message.reply_text("❌ দুঃখিত! ভিডিওটি পাওয়া যায়নি। ফাইল আইডিটি সঠিক নয়।")
    else:
        await update.message.reply_text("👋 হ্যালো! ভিডিও ডাউনলোড করতে দয়া করে আমাদের ওয়েবসাইট ব্যবহার করুন।")

async def get_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.video:
        video_file_id = update.message.video.file_id
        message_text = f"✅ **Your Video File ID is Ready!**\n\n" \
                       f"কোডটি কপি করে আপনার ওয়েবসাইটে বসান:\n" \
                       f"`{video_file_id}`\n\n" \
                       f"🔗 **আপনার ওয়েবসাইটের ডাউনলোড বাটনের লিংক হবে:**\n" \
                       f"https://t.me{context.bot.username}?start={video_file_id}"
        await update.message.reply_text(text=message_text, parse_mode="Markdown")

def main():
    Thread(target=run_flask).start()  
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.UpdateType.MESSAGE, get_file_id))  
    print("Bot started...")
    application.run_polling()

if __name__ == '__main__':
    main()
