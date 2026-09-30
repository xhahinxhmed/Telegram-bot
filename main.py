import asyncio
import re
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# ১. কনফিগারেশন (আপনার দেওয়া নতুন বটের টোকেন বসানো হয়েছে)
# ==========================================
BOT_TOKEN = "8960530766:AAGlXoTG82mtW7AIo8AvA6dEw9T9R0CdPKY"  

app = Flask('')

@app.route('/')
def home(): 
    return "Bot is Running 24/7 Alive and Secure!"

def run_flask(): 
    app.run(host='0.0.0.0', port=8080)

# ১৫ মিনিট পর ভিডিও ডিলিট করার ব্যাকগ্রাউন্ড ফাংশন
async def delete_message_after_delay(chat_id, message_id, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(900)  # ১৫ মিনিট = ৯০০ সেকেন্ড অপেক্ষা
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"Message {message_id} deleted successfully after 15 minutes.")
    except Exception as e:
        print(f"Error deleting message: {e}")

# ডীপ-লিঙ্কিং হ্যান্ডলার (ওয়েবসাইট থেকে ইউজার বাটনে ক্লিক করলে এখানে আসবে)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args  # ওয়েবসাইটের লিংকের শেষে থাকা File ID এখানে আসবে

    if args:
        file_id = args if isinstance(args, list) else args
        try:
            # ইউজারকে সরাসরি ভিডিও ফাইল পাঠানো হচ্ছে
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

# ফাইল আইডি এবং ডাউনলোড লিংক বের করার অ্যাডভান্সড ফাংশন (টাস্ক জ্যাম ফিক্সড)
async def catch_everything(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
        
    file_id = None
    
    # ক) যদি সরাসরি কোনো ছোট ভিডিও, ডকুমেন্ট বা অ্যানিমেশন বটের ইনবক্সে পাঠান
    if message.video: 
        file_id = message.video.file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('video/'):
        file_id = message.document.file_id
    elif message.animation:
        file_id = message.animation.file_id
        
    # খ) ট্রিকস: যদি চ্যানেলের ভিডিও লিংক টেক্সট আকারে বটে পাঠান
    elif message.text and ("t.me/" in message.text):
        link_parts = re.findall(r't\.me/(?:c/)?([^/]+)/(\d+)', message.text)
        if link_parts:
            channel_peer, msg_id = link_parts[0]
            message_id = int(msg_id)
            
            if channel_peer.isdigit():
                chat_target = int(f"-100{channel_peer}")
            else:
                chat_target = f"@{channel_peer}"
                
            try:
                # বট চ্যানেলের পোস্টটি ফরোয়ার্ড করে আইডি ক্যাচ করবে
                target_msg = await context.bot.forward_message(chat_id=message.chat_id, from_chat_id=chat_target, message_id=message_id)
                
                if target_msg.video: file_id = target_msg.video.file_id
                elif target_msg.document: file_id = target_msg.document.file_id
                elif target_msg.animation: file_id = target_msg.animation.file_id
                
                # আইডি নেওয়ার পর সাময়িক ফরোয়ার্ড মেসেজটি সাথে সাথে ডিলিট করে টাস্ক রিলিজ করা
                await context.bot.delete_message(chat_id=message.chat_id, message_id=target_msg.message_id)
            except Exception as e:
                await message.reply_text("❌ চ্যানেল থেকে ফাইল রিড করা যায়নি। নিশ্চিত হোন নতুন বটটি চ্যানেলের অ্যাডমিন কিনা।")
                return

    # ফাইল আইডি সফলভাবে পাওয়া গেলে আপনাকে চ্যাটে সুন্দর করে রিপ্লাই দেবে
    if file_id:
        # এখানে লিংক ফরম্যাট নিখুঁত করা হয়েছে (t.me/ এর পর স্ল্যাশ দেওয়া হয়েছে)
        message_text = f"✅ **আপনার ভিডিওর File ID সফলভাবে জেনারেট হয়েছে!**\n\n" \
                       f"📋 **File ID কোড (কপি করার প্রয়োজন নেই, নিচের রেডি লিংকটি নিন):**\n" \
                       f"`{file_id}`\n\n" \
                       f"🔗 **আপনার অ্যাডমিন প্যানেলে বসানোর ফাইনাল লিংক (এটি কপি করুন):**\n" \
                       f"https://t.me{context.bot.username}?start={file_id}"
                       
        await message.reply_text(text=message_text, parse_mode="Markdown")
    else:
        if message.text and "t.me/" not in message.text:
            await message.reply_text("👋 হ্যালো! ভিডিও ডাউনলোড করতে দয়া করে আমাদের ওয়েবসাইট ব্যবহার করুন।")

def main():
    Thread(target=run_flask).start()  
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL, catch_everything))  
    
    print("Bot started...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
