import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType
import asyncio
from flask import Flask
import threading

# Enable logging to see what's happening
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= CONFIGURATION =============
# Use environment variables for sensitive data
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8115639918:AAHhxPMwnhZKeELINimFB9Cry41KMn3KwIw')
TARGET_GROUP_INVITE_LINK = os.environ.get('TARGET_GROUP_LINK', 'https://t.me/movieprovider01')

# Message deletion settings
DELETE_AFTER_SECONDS = int(os.environ.get('DELETE_AFTER_SECONDS', '3600'))  # 1 hour default

# Customize your welcome message
WELCOME_MESSAGE = os.environ.get('WELCOME_MESSAGE', """
🎉 Welcome to our awesome group!

We're excited to have you here! 
To stay updated with all our latest discussions, please also join our main channel:

""")

# Flask app for health checks (required by Render)
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "running"}, 200

# ================================================

async def delete_message_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay_seconds: int):
    """Function to delete a message after specified delay"""
    try:
        await asyncio.sleep(delay_seconds)
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"🗑️ Deleted welcome message (ID: {message_id}) after {delay_seconds} seconds")
    except Exception as e:
        logger.error(f"❌ Could not delete message: {e}")

async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This function runs when someone joins the group"""
    try:
        # Check if this message is about new members joining
        if not update.message.new_chat_members:
            return
        
        # Check if this is happening in a group
        if update.effective_chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return
        
        # Welcome each new member
        for new_member in update.message.new_chat_members:
            # Skip if the new member is a bot
            if new_member.is_bot:
                continue
            
            # Create a button that links to your other group
            keyboard = [
                [InlineKeyboardButton("🔗 Join Main channel", url=TARGET_GROUP_INVITE_LINK)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Create welcome message with user's name
            welcome_text = f"👋 Hello {new_member.first_name}!\n{WELCOME_MESSAGE}"
            
            # Send the welcome message with button
            sent_message = await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup
            )
            
            logger.info(f"✅ Welcomed new member: {new_member.first_name}")
            logger.info(f"⏰ Message will be deleted after {DELETE_AFTER_SECONDS/3600} hour(s)")
            
            # Schedule message deletion
            asyncio.create_task(
                delete_message_after_delay(
                    context, 
                    sent_message.chat_id, 
                    sent_message.message_id, 
                    DELETE_AFTER_SECONDS
                )
            )
    
    except Exception as e:
        logger.error(f"❌ Error welcoming new member: {e}")

async def start_bot():
    """Start the Telegram bot"""
    logger.info("🤖 Starting Welcome Bot...")
    
    # Create the bot application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Tell the bot to run welcome_new_members when someone joins
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members)
    )
    
    logger.info("✅ Bot is ready and waiting for new members!")
    logger.info("📱 Add the bot to your group and make it an admin")
    
    # Start the bot with polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Keep the bot running
    try:
        await application.updater.idle()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    finally:
        await application.stop()

def run_flask():
    """Run Flask server in a separate thread"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

async def main():
    """Main function to start both Flask and Telegram bot"""
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"🌐 Flask server started on port {os.environ.get('PORT', 5000)}")
    
    # Start the Telegram bot
    await start_bot()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped")