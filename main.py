import asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# ১. কনফিগারেশন (আপনার বটের টোকেন বসানো হয়েছে)
# ==========================================
BOT_TOKEN = "8854706838:AAGGuJwBt--Dyh12BKyBJ7YljP_IpMvo2DM"  

# ==========================================
# ২. ২৪ ঘন্টা লাইভ রাখার জন্য ফ্লাস্ক সার্ভার
# ==========================================
app = Flask('')

@app.route('/')
def home(): 
    return "Bot is Running 24/7!"

def run_flask(): 
    app.run(host='0.0.0.0', port=8080)

# ==========================================
# ৩. ১৫ মিনিট পর ভিডিও ডিলিট করার ব্যাকগ্রাউন্ড ফাংশন
# ==========================================
async def delete_message_after_delay(chat_id, message_id, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(900)  # ১৫ মিনিট = ৯০০ সেকেন্ড অপেক্ষা করবে
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"Message {message_id} deleted successfully.")
    except Exception as e:
        print(f"Error deleting message: {e}")

# ==========================================
# ৪. স্টার্ট বাটন ও ডীপ-লিঙ্কিং হ্যান্ডলার (ইউজারদের ভিডিও পাঠানো)
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args  

    if args:
        file_id = args[0] if isinstance(args, list) else args
        try:
            sent_message = await context.bot.send_video(
                chat_id=chat_id, 
                video=file_id, 
                caption="🍿 আপনার কাঙ্ক্ষিত ভিডিওটি এখানে! এটি ১৫ মিনিট পর স্বয়ংক্রিয়ভাবে ডিলিট হয়ে যাবে।"
            )
            asyncio.create_task(delete_message_after_delay(chat_id, sent_message.message_id, context))
        except Exception as e:
            await update.message.reply_text("❌ দুঃখিত! ভিডিওটি পাওয়া যায়নি। ফাইল আইডিটি সঠিক নয়।")
            print(f"Error sending video: {e}")
    else:
        await update.message.reply_text("👋 হ্যালো! ভিডিও ডাউনলোড করতে দয়া করে আমাদের ওয়েবসাইট ব্যবহার করুন।")

# ==========================================
# ৫. ফাইল আইডি বের করার সর্বজনীন ফাংশন (সব ধরণের ফাইলের জন্য)
# ==========================================
async def get_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    file_id = None
    
    # ভিডিও, ডকুমেন্ট বা অ্যানিমেশন ফাইল—যা-ই আসুক তার আইডি বের করবে
    if message.video:
        file_id = message.video.file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.animation:
        file_id = message.animation.file_id
    elif message.audio:
        file_id = message.audio.file_id

    if file_id:
        message_text = f"✅ **আপনার ফাইলের আসল File ID পেয়ে গেছেন!**\n\n" \
                       f"কোডটি কপি করে রাখুন:\n" \
                       f"`{file_id}`\n\n" \
                       f"🔗 **ইউজারদের জন্য আপনার ডাউনলোড লিংক হবে:**\n" \
                       f"https://t.me{context.bot.username}?start={file_id}"
        await message.reply_text(text=message_text, parse_mode="Markdown")
    else:
        await message.reply_text("❌ এটি কোনো বৈধ ফাইল বা ভিডিও নয়। দয়া করে সঠিক ফাইল বা ভিডিও পাঠান।")

# ==========================================
# ৬. মেইন ফাংশন (বট চালু করার জায়গা)
# ==========================================
def main():
    Thread(target=run_flask).start()  
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    
    # এখানে filters.ALL দেওয়া হয়েছে যাতে যেকোনো ধরনের মেসেজ বট অবজেক্ট আকারে পায়
    application.add_handler(MessageHandler(filters.ALL, get_file_id))  
    
    print("Bot started...")
    
    # এই লাইনেallowed_updates দেওয়া হয়েছে যেন টেলিগ্রাম সব ধরণের ফাইল সার্ভারে পাঠায়
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
