import logging
import os
import json
import random
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Load environment variables
load_dotenv()

# Your bot token obtained from BotFather
TOKEN = os.getenv("BOT_TOKEN")

# Define states for conversation
MENU, flirt, picture, bubble, motivation, location, stats, reminder = range(8)

# Set up logging for the bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Helper function to load JSON data
def load_json_data(filename: str) -> dict:
    """Load JSON data from a file in the same directory as the script."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, filename)
        
        with open(json_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return {}
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return {}

# Flirt handler function
async def handle_flirt(query) -> None:
    """Handle flirt button click and send a random flirt message."""
    try:
        data = load_json_data('flirt_database.json')
        
        if 'flirt_messages' not in data or not data['flirt_messages']:
            await query.edit_message_text(text="sorry, i'm feeling a bit tongue-tied right now! 😅")
            return
        
        flirt_messages = data['flirt_messages']
        random_flirt = random.choice(flirt_messages)
        
        await query.edit_message_text(text=random_flirt)
    except Exception as e:
        logger.error(f"Error in handle_flirt: {e}")
        await query.edit_message_text(text="oops! something went wrong with my rizz game 😬")

# Picture handler function
async def handle_picture(query) -> int:
    """Handle picture button click."""
    await query.edit_message_text(text="you selected 'i wanna see you'... sorry bro, no pics yet 📸")
    return ConversationHandler.END

# Bubble handler function
async def handle_bubble(query) -> int:
    """Handle bubble button click."""
    await query.edit_message_text(text="you want a bubble? here's one: 🫧 *pop*")
    return ConversationHandler.END

# Motivation handler function
async def handle_motivation(query) -> int:
    """Handle motivation button click."""
    await query.edit_message_text(text="eh bro, life tough but you tougher lah! keep going 💪")
    return ConversationHandler.END

# Location handler function
async def handle_location(query) -> int:
    """Handle location button click."""
    await query.edit_message_text(text="i'm everywhere and nowhere at the same time... very deep right 🌍")
    return ConversationHandler.END

# Stats handler function
async def handle_stats(query) -> int:
    """Handle stats button click."""
    await query.edit_message_text(text="stats: 100% good looking, 200% humble 📊")
    return ConversationHandler.END

# Reminder handler function
async def handle_reminder(query) -> int:
    """Handle reminder button click."""
    await query.edit_message_text(text="reminder set: remember to be awesome today! ⏰")
    return ConversationHandler.END

# Start command handler
async def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("gimme some rizz", callback_data="flirt")],
        [InlineKeyboardButton("i wanna see you", callback_data="picture")],
        [InlineKeyboardButton("i want a bubble", callback_data="bubble")],
        [InlineKeyboardButton("i'm sad, give me motivation", callback_data="motivation")],
        [InlineKeyboardButton("where are you?", callback_data="location")],
        [InlineKeyboardButton("show some stats", callback_data="stats")],
        [InlineKeyboardButton("set a reminder", callback_data="reminder")],
        [InlineKeyboardButton("cancel", callback_data="cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome! Please choose an option:", reply_markup=reply_markup
    )
    return MENU

# Button click handler
async def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "flirt":
        await handle_flirt(query)
        return ConversationHandler.END
    elif query.data == "picture":
        return await handle_picture(query)
    elif query.data == "bubble":
        return await handle_bubble(query)
    elif query.data == "motivation":
        return await handle_motivation(query)
    elif query.data == "location":
        return await handle_location(query)
    elif query.data == "stats":
        return await handle_stats(query)
    elif query.data == "reminder":
        return await handle_reminder(query)
    elif query.data == "cancel":
        await query.edit_message_text(text="operation cancelled.")
        return ConversationHandler.END
    else:
        await query.edit_message_text(text="unknown option selected.")
        return MENU

# Cancel handler
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# Main function to start the bot
def main():
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .read_timeout(10)
        .write_timeout(10)
        .concurrent_updates(True)
        .build()
    )

    # ConversationHandler to handle the state machine
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(button)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()