import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from ai import analyze_forwarded_message
from dotenv import load_dotenv

load_dotenv()

# Enable logging to see what's happening
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    
    if not message.forward_origin:
        return
    
    original_sender = None
    original_sender_name = None
    current_sender = message.from_user
    
    if hasattr(message.forward_origin, 'sender_user') and message.forward_origin.sender_user:
        original_sender = message.forward_origin.sender_user
        original_sender_name = f"@{original_sender.username}" if original_sender.username else original_sender.first_name
    elif hasattr(message.forward_origin, 'sender_user_name'):
        original_sender_name = message.forward_origin.sender_user_name
    elif hasattr(message.forward_origin, 'chat') and message.forward_origin.chat:
        original_sender_name = message.forward_origin.chat.title or message.forward_origin.chat.username
    
    if not original_sender_name:
        await message.reply_text("Could not determine original sender of forwarded message.")
        return
    
    message_text = message.text or message.caption or ""
    current_sender_name = f"@{current_sender.username}" if current_sender.username else current_sender.first_name
    
    try:
        analysis_result = await analyze_forwarded_message(original_sender_name, current_sender_name, message_text)
        await message.reply_text(analysis_result)
        
    except Exception as e:
        logging.error(f"Error analyzing message: {e}")
        await message.reply_text(f"Error analyzing message: {str(e)}")


def main():
    token = os.getenv("TOKEN")
    if not token:
        print("ERROR: TOKEN environment variable not set!")
        return
    
    print("Starting bot...")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded_message))
    
    # This handles the event loop internally
    print("Bot is running. Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main() 