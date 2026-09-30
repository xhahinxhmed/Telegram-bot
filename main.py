import asyncio
import re
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# ১. কনফিগারেশন (আপনার বটের আসল টোকেন)
# ==========================================
BOT_TOKEN = "8854706838:AAGGuJwBt--Dyh12BKyBJ7YljP_IpMvo2DM"  

# ==========================================
# ২. ২৪ ঘন্টা লাইভ রাখার জন্য ফ্লাস্ক সার্ভার
# ==========================================
app = Flask('')

@app.route('/')
def home(): 
    return "Bot is Running 24/7 Alive!"

def run_flask(): 
    app.run(host='0.0.0.0', port=8080)

# ==========================================
# ৩. ১৫ মিনিট পর ভিডিও ডিলিট করার ব্যাকগ্রাউন্ড ফাংশন
# ==========================================
async def delete_message_after_delay(chat_id, message_id, context: ContextTypes.DEFAULT_TYPE):
    # ১৫ মিনিট = ৯০০ সেকেন্ড অপেক্ষা করবে
    await asyncio.sleep(900)  
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"Message {message_id} deleted successfully after 15 minutes.")
    except Exception as e:
        print(f"Error deleting message: {e}")

# ==========================================
# ৪. ডীপ-লিঙ্কিং হ্যান্ডলার (ওয়েবসাইট থেকে ইউজার বাটনে ক্লিক করলে ভিডিও পাবে)
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args  # ওয়েবসাইটের লিংকের শেষে থাকা File ID এখানে আসবে

    if args:
        file_id = args[0] if isinstance(args, list) else args
        try:
            # ইউজারকে সরাসরি File ID ব্যবহার করে ভিডিও পাঠানো হচ্ছে (১ সেকেন্ডে চলে যাবে)
            sent_message = await context.bot.send_video(
                chat_id=chat_id, 
                video=file_id, 
                caption="🍿 **আপনার কাঙ্ক্ষিত ভিডিওটি এখানে! এটি ১৫ মিনিট পর স্বয়ংক্রিয়ভাবে মুছে যাবে।**\n\n⚠️ *দয়া করে এর মধ্যে ভিডিওটি দেখে নিন বা সেভ করে নিন।*"
            )
            # ভিডিও পাঠানোর সাথে সাথেই ১৫ মিনিটের টাইমার চালু হবে
            asyncio.create_task(delete_message_after_delay(chat_id, sent_message.message_id, context))
        except Exception as e:
            await update.message.reply_text("❌ দুঃখিত! ভিডিওটি পাওয়া যায়নি। ফাইল আইডিটি সঠিক নয় বা ভিডিওটি সার্ভার থেকে মুছে গেছে।")
            print(f"Error sending video: {e}")
    else:
        await update.message.reply_text("👋 হ্যালো! ভিডিও ডাউনলোড করতে দয়া করে আমাদের ওয়েবসাইট ব্যবহার করুন।")

# ==========================================
# ৫. ফাইল আইডি এবং ডাউনলোড লিংক বের করার অ্যাডভান্সড ফাংশন
# ==========================================
async def catch_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    file_id = None
    
    # ক) যদি আপনি সরাসরি ছোট ভিডিও, ডকুমেন্ট বা অ্যানিমেশন বটের ইনবক্সে পাঠান
    if message.video: 
        file_id = message.video.file_id
    elif message.document and message.document.mime_type.startswith('video/'):
        file_id = message.document.file_id
    elif message.animation:
        file_id = message.animation.file_id
        
    # খ) ট্রিকস: যদি আপনি চ্যানেলের ভিডিও লিংক টেক্সট আকারে বটে পাঠান
    elif message.text and ("t.me/" in message.text):
        # লিংক থেকে চ্যানেল আইডি এবং মেসেজ আইডি আলাদা করার চেষ্টা
        link_parts = re.findall(r't\.me/(?:c/)?([^/]+)/(\053?\d+)', message.text)
        if link_parts:
            channel_peer = link_parts[0][0]
            message_id = int(link_parts[0][1])
            
            # যদি প্রাইভেট চ্যানেল হয় (যেমন c/123456) তাহলে মাইনাস ১০০ যোগ করতে হয় টেলিগ্রাম রুলস অনুযায়ী
            if channel_peer.isdigit():
                chat_target = int(f"-100{channel_peer}")
            else:
                chat_target = f"@{channel_peer}"
                
            try:
                # বট আপনার হয়ে ওই চ্যানেলের পোস্টটি রিমোটলি চেক করবে
                target_msg = await context.bot.get_custom_emoji_stickers if hasattr(context.bot, 'get_discussion_message') else await context.bot.forward_message(chat_id=chat_id, from_chat_id=chat_target, message_id=message_id)
                
                # ফরোয়ার্ড করা মেসেজ থেকে ফাইল আইডি নেওয়া
                if target_msg.video: file_id = target_msg.video.file_id
                elif target_msg.document: file_id = target_msg.document.file_id
                
                # সাময়িক ফরোয়ার্ড মেসেজটি সাথে সাথে ডিলিট করে দেওয়া (ক্লিন রাখার জন্য)
                await context.bot.delete_message(chat_id=chat_id, message_id=target_msg.message_id)
            except Exception as e:
                pass

    # ফাইল আইডি সফলভাবে পাওয়া গেলে আপনাকে রিপ্লাই দেবে
    if file_id:
        message_text = f"✅ **আপনার ভিডিওর File ID সফলভাবে জেনারেট হয়েছে!**\n\n" \
                       f"📋 **File ID কোড (কপি করে রাখুন):**\n" \
                       f"`{file_id}`\n\n" \
                       f"🔗 **আপনার HTML ওয়েবসাইটের ডাউনলোড বাটনের ফাইনাল লিংক:**\n" \
                       f"https://t.me{context.bot.username}?start={file_id}"
                       
        await message.reply_text(text=message_text, parse_mode="Markdown")
    else:
        # সাধারণ মেসেজ বা টেক্সট আসলে ওয়েবসাইট ব্যবহারের নোটিশ দেবে
        await message.reply_text("👋 হ্যালো! ভিডিও ডাউনলোড করতে দয়া করে আমাদের ওয়েবসাইট ব্যবহার করুন।")

# ==========================================
# ৬. মেইন ফাংশন (বট রান ও Polling শুরু)
# ==========================================
def main():
    # ব্যাকগ্রাউন্ডে ফ্লাস্ক ওয়েব সার্ভার চালু করা (Keep Alive)
    Thread(target=run_flask).start()  
    
    # বট অ্যাপ্লিকেশন তৈরি
    application = Application.builder().token(BOT_TOKEN).build()
    
    # হ্যান্ডলারগুলো যুক্ত করা
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL, catch_everything))  
    
    print("Bot started...")
    # সব ধরণের ফাইল আপডেট রিসিভ করার পারমিশন চালু
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
