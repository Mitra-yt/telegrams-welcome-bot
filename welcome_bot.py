import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram.constants import ChatType

# ============= Configure Logging =============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============= Configuration =============
BOT_TOKEN = os.environ['BOT_TOKEN']  # Must be set in Render
TARGET_GROUP_INVITE_LINK = os.environ.get('TARGET_GROUP_LINK', 'https://t.me/movieprovider01')
DELETE_AFTER_SECONDS = int(os.environ.get('DELETE_AFTER_SECONDS', 3600))  # 1 hour default

WELCOME_MESSAGE = os.environ.get('WELCOME_MESSAGE', """
🎉 Welcome to our awesome group!

We're excited to have you here! 
To stay updated with all our latest discussions, please join our main channel:
""")

# ============= Bot Functions =============
async def delete_message_after_delay(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, delay_seconds: int):
    """Delete message after specified delay"""
    try:
        await asyncio.sleep(delay_seconds)
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Deleted welcome message (ID: {message_id})")
    except Exception as e:
        logger.error(f"Delete failed: {e}")

async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new group members"""
    try:
        if not update.message or not update.message.new_chat_members:
            return
        
        if update.effective_chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return
        
        for new_member in update.message.new_chat_members:
            if new_member.is_bot:
                continue
            
            keyboard = [[InlineKeyboardButton("🔗 Join Main Channel", url=TARGET_GROUP_INVITE_LINK)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_text = f"👋 Hello {new_member.first_name}!\n{WELCOME_MESSAGE}"
            sent_message = await update.message.reply_text(welcome_text, reply_markup=reply_markup)
            
            logger.info(f"Welcomed: {new_member.first_name}")
            asyncio.create_task(
                delete_message_after_delay(
                    context, 
                    sent_message.chat_id, 
                    sent_message.message_id, 
                    DELETE_AFTER_SECONDS
                )
            )
    except Exception as e:
        logger.error(f"Welcome error: {e}")

# ============= Bot Startup =============
async def start_bot():
    """Main bot startup function"""
    logger.info("Starting Telegram bot...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    logger.info("Bot is now running")
    
    # Keep running until stopped
    while True:
        await asyncio.sleep(3600)  # Sleep instead of idle to avoid thread issues

def run_bot():
    """Run bot in asyncio event loop"""
    asyncio.run(start_bot())

if __name__ == '__main__':
    run_bot()
