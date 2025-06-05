import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)

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
    
    prompt = f"""
    Analyze this forwarded message for potential account impersonation or compromise:
    
    Original sender: {original_sender_name}
    Current sender: {current_sender_name}
    Message content: "{message_text}"
    
    Look for signs of:
    1. Account compromise/hacking (suspicious content that doesn't match typical user behavior)
    2. Impersonation attempts (claiming to be someone else)
    3. Scam messages (phishing, fake giveaways, suspicious links)
    4. Unusual language patterns or requests
    
    If you detect potential compromise/impersonation, respond with:
    "🚨 POTENTIAL ACCOUNT COMPROMISE DETECTED
    
    Compromised account: [username/name]
    Indicators: [specific reasons for suspicion]
    Recommendation: [what users should do]"
    
    If the message appears legitimate, respond with:
    "✅ Message appears legitimate - no signs of compromise detected."
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        
        analysis_result = response.choices[0].message.content
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
