import logging
import os
import json
import random
import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
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
MENU, WAITING_REMINDER_TEXT, WAITING_REMINDER_TIME, WAITING_PHOTO_UPLOAD, WAITING_BUBBLE_TEXT, WAITING_VIDEO_UPLOAD, WAITING_NAME_INPUT, DEFAULT = range(8)

# Set up logging for the bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Helper function to load JSON data
def load_json_data(filename: str) -> dict:
    """
    Load JSON data from a file in the same directory as the script.
    
    Args:
        filename (str): Name of the JSON file to load
        
    Returns:
        dict: Loaded JSON data or empty dict if error occurs
    """
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

def save_json_data(filename: str, data: dict) -> bool:
    """
    Save JSON data to a file in the same directory as the script.
    
    Args:
        filename (str): Name of the JSON file to save
        data (dict): Data to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, filename)
        
        with open(json_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving {filename}: {e}")
        return False

def calculate_days_between(start_date: str, end_date: str) -> int:
    """
    Calculate days between two dates.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        int: Number of days between dates
    """
    try:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days
    except Exception as e:
        logger.error(f"Error calculating days: {e}")
        return 0

def days_from_today(target_date: str) -> int:
    """
    Calculate days from today to target date.
    
    Args:
        target_date (str): Target date in YYYY-MM-DD format
        
    Returns:
        int: Number of days (negative if in past, positive if in future)
    """
    try:
        today = datetime.datetime.now().date()
        target = datetime.datetime.strptime(target_date, "%Y-%m-%d").date()
        return (target - today).days
    except Exception as e:
        logger.error(f"Error calculating days from today: {e}")
        return 0

def get_user_role(user_id: int) -> Optional[str]:
    """
    Get the role of a user (boyfriend or girlfriend).
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        Optional[str]: User role ('boyfriend' or 'girlfriend') or None if not set
    """
    try:
        data = load_json_data('bot_data.json')
        user_roles = data.get('user_roles', {})
        return user_roles.get(str(user_id))
    except Exception as e:
        logger.error(f"Error getting user role: {e}")
        return None

def get_user_name(user_id: int) -> Optional[str]:
    """
    Get the name of a user.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        Optional[str]: User name or None if not set
    """
    try:
        data = load_json_data('bot_data.json')
        user_names = data.get('user_names', {})
        return user_names.get(str(user_id))
    except Exception as e:
        logger.error(f"Error getting user name: {e}")
        return None

def set_user_name(user_id: int, name: str) -> bool:
    """
    Set the name of a user.
    
    Args:
        user_id (int): Telegram user ID
        name (str): Name to set
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = load_json_data('bot_data.json')
        if 'user_names' not in data:
            data['user_names'] = {}
        
        data['user_names'][str(user_id)] = name
        return save_json_data('bot_data.json', data)
    except Exception as e:
        logger.error(f"Error setting user name: {e}")
        return False

def set_user_role(user_id: int, role: str) -> bool:
    """
    Set the role of a user.
    
    Args:
        user_id (int): Telegram user ID
        role (str): Role to set ('boyfriend' or 'girlfriend')
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = load_json_data('bot_data.json')
        if 'user_roles' not in data:
            data['user_roles'] = {}
        
        data['user_roles'][str(user_id)] = role
        return save_json_data('bot_data.json', data)
    except Exception as e:
        logger.error(f"Error setting user role: {e}")
        return False

def get_role_based_content(content_type: str, user_role: str) -> list:
    """
    Get content based on user role.
    
    Args:
        content_type (str): Type of content (e.g., 'image_paths', 'telebubbles')
        user_role (str): User role ('boyfriend' or 'girlfriend')
        
    Returns:
        list: List of content items for the user's role
    """
    try:
        data = load_json_data('bot_data.json')
        
        # Try to get role-specific content first
        if 'content' in data and user_role in data['content']:
            role_content = data['content'][user_role].get(content_type, [])
            if role_content:
                return role_content
        
        # Fall back to general content if role-specific doesn't exist
        return data.get(content_type, [])
    except Exception as e:
        logger.error(f"Error getting role-based content: {e}")
        return []

def save_content_for_partner(content_type: str, content_data: any, submitter_role: str) -> bool:
    """
    Save content submitted by one partner for the other.
    
    Args:
        content_type (str): Type of content being saved
        content_data (any): The content to save
        submitter_role (str): Role of the person submitting ('boyfriend' or 'girlfriend')
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = load_json_data('bot_data.json')
        
        # Initialize content structure if it doesn't exist
        if 'content' not in data:
            data['content'] = {
                'boyfriend': {},
                'girlfriend': {}
            }
        
        # Determine partner's role
        partner_role = 'girlfriend' if submitter_role == 'boyfriend' else 'boyfriend'
        
        # Initialize content type array if it doesn't exist
        if content_type not in data['content'][partner_role]:
            data['content'][partner_role][content_type] = []
        
        # Add the new content
        data['content'][partner_role][content_type].append(content_data)
        
        return save_json_data('bot_data.json', data)
    except Exception as e:
        logger.error(f"Error saving content for partner: {e}")
        return False

async def show_main_menu_from_query(query) -> int:
    """
    Helper function to show main menu from a callback query.
    Handles both text messages and photo messages properly.
    Shows role-based menu options.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: MENU state
    """
    user_id = query.from_user.id
    user_role = get_user_role(user_id)
    
    # Base menu options
    keyboard = [
        [InlineKeyboardButton(" gimme some rizz", callback_data="flirt")],
        [InlineKeyboardButton("📸 i wanna see you", callback_data="picture")],
        [InlineKeyboardButton("🫧 i want a bubble", callback_data="bubble")],
        [InlineKeyboardButton("💪 i need motivation", callback_data="motivation")],
        [InlineKeyboardButton(" show me our stats", callback_data="stats")],
        [InlineKeyboardButton("⏰ set a reminder", callback_data="reminder")],
        [InlineKeyboardButton("🍽️ where should we eat?", callback_data="restaurant")]
    ]
    
    # Add role-specific submission options
    if user_role:
        keyboard.extend([
            [InlineKeyboardButton("📤 submit photo for partner", callback_data="submit_photo")],
            [InlineKeyboardButton("🫧 submit bubble for partner", callback_data="submit_bubble")],
        ])
    
    # Role management and exit options
    if not user_role:
        keyboard.extend([
            [InlineKeyboardButton("👤 set my role", callback_data="set_role")],
            [InlineKeyboardButton("❌ exit bot", callback_data="exit")]
        ])
    else:
        keyboard.extend([
            [InlineKeyboardButton(f"👤 role: {user_role}", callback_data="change_role")],
            [InlineKeyboardButton("❌ exit bot", callback_data="exit")]
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if user_role:
        back_message = (
            f"💫 **back to the main menu!** 💫\n"
            f"role: **{user_role}** 👤\n\n"
            "what would you like to do next? ✨"
        )
    else:
        back_message = (
            "💫 **welcome to the main menu!** 💫\n"
            "⚠️ please set your role first to access all features! 💕\n\n"
            "what would you like to do? ✨"
        )
    
    try:
        # Check if the message has text content that can be edited
        if query.message.text is not None:
            # Message has text, we can edit it
            await query.edit_message_text(
                back_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            # Message is a photo or other media, delete it and send new text message
            await query.message.reply_text(
                back_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    except Exception as e:
        logger.error(f"Error in show_main_menu_from_query: {e}")
        # Fallback: delete and send new message
        try:
            await query.message.delete()
            await query.message.reply_text(
                back_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as fallback_error:
            logger.error(f"Fallback error in show_main_menu_from_query: {fallback_error}")
            # Last resort: just send a new message
            await query.message.reply_text(
                back_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    return MENU

# Flirt handler function
async def handle_flirt(query) -> int:
    """
    Handle flirt button click and send a random flirt message.
    Loads flirt messages from bot_data.json and sends a random one.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: MENU to return to main menu after showing flirt message
    """
    try:
        data = load_json_data('bot_data.json')
        
        if 'flirt_messages' not in data or not data['flirt_messages']:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="sorry, i'm feeling a bit tongue-tied right now! 😅",
                reply_markup=reply_markup
            )
            return MENU
        
        flirt_messages = data['flirt_messages']
        random_flirt = random.choice(flirt_messages)
        
        # Create inline keyboard with back to menu option
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"💕 {random_flirt}",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in handle_flirt: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="oops! something went wrong with my rizz game... L rizz 😬",
            reply_markup=reply_markup
        )
    
    return MENU

# Picture handler function
async def handle_picture(query) -> int:
    """
    Handle picture button click and send a random image based on user role.
    Loads image paths from bot_data.json and sends a random image if available.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: MENU to return to main menu after sending picture
    """
    try:
        user_id = query.from_user.id
        user_role = get_user_role(user_id)
        
        if not user_role:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="⚠️ please set your role first using the 'set my role' button to access pictures! 💕",
                reply_markup=reply_markup
            )
            return MENU
        
        # Get role-specific images
        image_paths = get_role_based_content('image_paths', user_role)
        
        if not image_paths:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="sorry babe, no pics available right now 📸 but imagine me winking at you 😉\n\n(your partner hasn't submitted any photos for you yet!)",
                reply_markup=reply_markup
            )
            return MENU
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Find available images
        available_images = []
        for img_path in image_paths:
            full_path = os.path.join(script_dir, img_path)
            if os.path.exists(full_path):
                available_images.append(full_path)
        
        if not available_images:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="oops! seems like i'm camera shy today 📸😅 check back later!\n\n(some image files might be missing)",
                reply_markup=reply_markup
            )
            return MENU
        
        # Send random image
        random_image = random.choice(available_images)
        
        # Delete the original message first
        await query.delete_message()
        
        # Create keyboard for back to menu
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the photo
        with open(random_image, 'rb') as photo:
            await query.message.reply_photo(
                photo=photo,
                caption="here's a little something to brighten your day! 📸✨\n(submitted by your partner 💕)",
                reply_markup=reply_markup
            )
    
    except Exception as e:
        logger.error(f"Error in handle_picture: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="oops! something went wrong with the camera 📸💔",
            reply_markup=reply_markup
        )
    
    return MENU

# Bubble handler function
async def handle_bubble(query) -> int:
    """
    Handle bubble button click and send a random video bubble based on user role.
    Loads video messages from bot_data.json and sends a random video.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: MENU to return to main menu after showing bubble
    """
    try:
        user_id = query.from_user.id
        user_role = get_user_role(user_id)
        
        if not user_role:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="⚠️ please set your role first using the 'set my role' button to access bubbles! 💕",
                reply_markup=reply_markup
            )
            return MENU
        
        # Get role-specific video messages only
        video_messages = get_role_based_content('video_messages', user_role)
        
        if not video_messages:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="🫧 *pop* no video bubbles available right now! 😅\n\n(your partner hasn't submitted any video bubbles for you yet! 💕)",
                reply_markup=reply_markup
            )
            return MENU
        
        # Select random video
        random_video = random.choice(video_messages)
        
        # Create inline keyboard with back to menu option
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        video_path = os.path.join(script_dir, random_video)
        
        if os.path.exists(video_path):
            # Delete the original message first
            await query.delete_message()
            
            # Send the video
            with open(video_path, 'rb') as video:
                await query.message.reply_video(
                    video=video,
                    caption="🫧 here's a video bubble from your partner! 💕✨",
                    reply_markup=reply_markup
                )
        else:
            await query.edit_message_text(
                text="🫧 video bubble not found, but here's love anyway! 💕",
                reply_markup=reply_markup
            )
    
    except Exception as e:
        logger.error(f"Error in handle_bubble: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🫧 *pop* here's a bubble full of love even though something went wrong! 💕",
            reply_markup=reply_markup
        )
    
    return MENU

# Motivation handler function
async def handle_motivation(query) -> int:
    """
    Handle motivation button click and send an encouraging pep talk.
    Loads pep talk messages from bot_data.json and sends a random motivational message.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: MENU to return to main menu after showing motivation
    """
    try:
        data = load_json_data('bot_data.json')
        
        if 'pep_talks' not in data or not data['pep_talks']:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="eh bro, life tough but you tougher lah! keep going 💪",
                reply_markup=reply_markup
            )
            return MENU
        
        pep_talks = data['pep_talks']
        random_pep_talk = random.choice(pep_talks)
        
        # Create inline keyboard with back to menu option
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"💪 {random_pep_talk}",
            reply_markup=reply_markup
        )
    
    except Exception as e:
        logger.error(f"Error in handle_motivation: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="hey, even when things go wrong, you're still amazing! keep your head up! 💪✨",
            reply_markup=reply_markup
        )
    
    return MENU

# Stats handler function
async def handle_stats(query) -> int:
    """
    Handle stats button click and display relationship/exchange statistics.
    Shows days left in exchange, relationship duration, and days until next meeting.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: MENU to return to main menu after showing stats
    """
    try:
        data = load_json_data('bot_data.json')
        
        if 'exchange_stats' not in data:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="📊 stats: 100% in love, 200% missing you, ∞% worth it 💕",
                reply_markup=reply_markup
            )
            return MENU
        
        stats = data['exchange_stats']
        today = datetime.datetime.now().date().strftime("%Y-%m-%d")
        
        # Calculate various statistics
        exchange_days_left = days_from_today(stats.get('end_date', ''))
        relationship_days = calculate_days_between(stats.get('relationship_start', ''), today)
        days_until_meeting = days_from_today(stats.get('next_meeting', ''))
        
        # Format the statistics message
        stats_message = "📊 **our statistics!** 📊\n\n"
        
        if exchange_days_left > 0:
            stats_message += f"🎓 exchange days left: **{exchange_days_left} days** ⏰\n"
        elif exchange_days_left == 0:
            stats_message += f"🎓 exchange ends: **today!** 🎉\n"
        else:
            stats_message += f"🎓 exchange completed **{abs(exchange_days_left)} days ago** ✅\n"

        if relationship_days > 0:
            years = relationship_days // 365
            remaining_days = relationship_days % 365
            months = relationship_days // 30
            remaining_days = relationship_days % 30
            if years > 0:
                stats_message += f"💕 together for: **{years} year(s), {remaining_days} days** 🥰\n"
            elif months > 0:
                stats_message += f"💕 together for: **{months} month(s), {remaining_days} days** 🥰\n"
            else:
                stats_message += f"💕 together for: **{relationship_days} days** 🥰\n"
        
        if days_until_meeting > 0:
            stats_message += f"✈️ days until we meet: **{days_until_meeting} days** 🤗\n"
        elif days_until_meeting == 0:
            stats_message += f"✈️ omggg meeting day: **today!** 🥳\n"
        else:
            stats_message += f"✈️ last met **{abs(days_until_meeting)} days ago** 🥺\n"
        
        stats_message += f"\n💫 statistically, love level: **100/10!!!** 💫"
        
        # Create inline keyboard with back to menu option
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=stats_message, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    except Exception as e:
        logger.error(f"Error in handle_stats: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="📊 stats: 100% good looking, 200% humble, ∞% in love with you 💕",
            reply_markup=reply_markup
        )
    
    return MENU

# Reminder handler function
async def handle_reminder(query) -> int:
    """
    Handle reminder button click and start reminder creation process.
    This initiates a conversation to set up a reminder.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: WAITING_REMINDER_TEXT state to continue conversation
    """
    try:
        await query.edit_message_text(
            text="💌 what would you like me to remind you about? just type your reminder message!\n\n_(type /cancel to go back to menu)_"
        )
        return WAITING_REMINDER_TEXT
    
    except Exception as e:
        logger.error(f"Error in handle_reminder: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="oops! reminder system is taking a nap 😴 try again later!",
            reply_markup=reply_markup
        )
        return MENU

async def process_reminder_text(update: Update, context: CallbackContext) -> int:
    """
    Process the reminder text input from user.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: WAITING_REMINDER_TIME state to continue conversation
    """
    try:
        reminder_text = update.message.text
        context.user_data['reminder_text'] = reminder_text
        
        await update.message.reply_text(
            f"📝 got it! reminder: \"{reminder_text}\" ✨\n\n"
            "⏰ when should i remind you? send me the time in format:\n"
            "• **HH:MM** (e.g., 14:30 for 2:30 PM) 🕐\n"
            "• or just say **now** for immediate reminder ⚡\n"
            "• or **tomorrow** for same time tomorrow 📅\n\n"
            "_(type /cancel to go back to menu)_ 💕",
            parse_mode='Markdown'
        )
        return WAITING_REMINDER_TIME
    
    except Exception as e:
        logger.error(f"Error processing reminder text: {e}")
        await update.message.reply_text("oops! something went wrong. let's start over with /start")
        return MENU

async def process_reminder_time(update: Update, context: CallbackContext) -> int:
    """
    Process the reminder time input and save the reminder.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: MENU to return to main menu after setting reminder
    """
    try:
        time_input = update.message.text.lower()
        reminder_text = context.user_data.get('reminder_text', 'generic reminder')
        
        # Create back to menu keyboard
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Simple reminder processing (in a real bot, you'd use proper scheduling)
        if time_input == "now":
            await update.message.reply_text(
                f"⏰ **reminder:** {reminder_text} 🔔", 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        elif time_input == "tomorrow":
            await update.message.reply_text(
                f"✅ reminder set for tomorrow: \"{reminder_text}\" 📅\n"
                "📝 (note: this is a demo - real scheduling would be implemented with proper task scheduler) 💻",
                reply_markup=reply_markup
            )
        elif ":" in time_input:
            await update.message.reply_text(
                f"✅ reminder set for {time_input}: \"{reminder_text}\" ⏰\n"
                "📝 (note: this is a demo - real scheduling would be implemented with proper task scheduler) 💻",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                f"⏰ reminder noted: \"{reminder_text}\" 📝\n"
                "� i'll try to remember that for you! (this is a demo feature) ✨",
                reply_markup=reply_markup
            )
        
        return MENU
    
    except Exception as e:
        logger.error(f"Error processing reminder time: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "oops! reminder system had a hiccup 😅 but i'll try to remember anyway!",
            reply_markup=reply_markup
        )
        return MENU

# Restaurant suggestion handler
async def handle_restaurant(query) -> int:
    """
    Handle restaurant suggestion button and provide dining recommendations.
    Loads restaurant data from bot_data.json and suggests a random place to eat.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: MENU to return to main menu after showing restaurant suggestion
    """
    try:
        data = load_json_data('bot_data.json')
        
        if 'restaurant_suggestions' not in data or not data['restaurant_suggestions']:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="🍜 how about we cook together instead? i'll bring the love, you bring the appetite! 👨‍🍳💕",
                reply_markup=reply_markup
            )
            return MENU
        
        restaurants = data['restaurant_suggestions']
        random_restaurant = random.choice(restaurants)
        
        restaurant_message = f"🍽️ **{random_restaurant['name']}** 🍽️\n\n"
        restaurant_message += f"📍 type: {random_restaurant['type']} 🏷️\n"
        restaurant_message += f"📝 {random_restaurant['description']} ✨\n"
        restaurant_message += f"⭐ rating: {random_restaurant['rating']} 🌟\n"
        restaurant_message += f"✨ vibe: {random_restaurant['vibe']} 💫\n\n"
        restaurant_message += "bon appétit, babe! 😘🍴"
        
        # Create inline keyboard with back to menu option
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=restaurant_message, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    except Exception as e:
        logger.error(f"Error in handle_restaurant: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🍜 error finding restaurants, but anywhere with you would be perfect! 💕",
            reply_markup=reply_markup
        )
    
    return MENU

# Role management handlers
async def handle_set_role(query) -> int:
    """
    Handle role setting button click.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: MENU to return to main menu after role selection
    """
    try:
        keyboard = [
            [InlineKeyboardButton("💙 i'm the boyfriend", callback_data="role_boyfriend")],
            [InlineKeyboardButton("💖 i'm the girlfriend", callback_data="role_girlfriend")],
            [InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text="👤 **choose your role:**\n\nthis will determine what content you see and can submit! 💕",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in handle_set_role: {e}")
        return await show_main_menu_from_query(query)
    
    return MENU

async def handle_role_selection(query, role: str) -> int:
    """
    Handle role selection (boyfriend or girlfriend) and ask for name.
    
    Args:
        query: Telegram callback query object
        role: Selected role ('boyfriend' or 'girlfriend')
        
    Returns:
        int: WAITING_NAME_INPUT to wait for name input
    """
    try:
        await query.edit_message_text(
            text=f"✨ okay ur the **{role}**! ✨\n\n"
                 f"sooo... what's your name... i mean i know already but i need to put it in the software 💕\n\n"
                 f"_(type /cancel to go back to menu)_",
            parse_mode='Markdown'
        )
        return WAITING_NAME_INPUT
    except Exception as e:
        logger.error(f"Error in handle_role_selection: {e}")
        return await show_main_menu_from_query(query)

async def process_name_input(update: Update, context: CallbackContext) -> int:
    """
    Process the name input from user and complete role setup.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: MENU to return to main menu after setting role and name
    """
    try:
        user_id = update.effective_user.id
        name = update.message.text.strip()
        
        # Get the selected role from context or determine from button press
        # We'll need to track this differently - let's use a simple approach
        # For now, let's ask them to choose role again with their name
        
        keyboard = [
            [InlineKeyboardButton(f"💙 i'm {name}, the boyfriend", callback_data=f"confirm_boyfriend_{name}")],
            [InlineKeyboardButton(f"💖 i'm {name}, the girlfriend", callback_data=f"confirm_girlfriend_{name}")],
            [InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"okay **{name}** just to confirm ah: 😊\n\n",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return MENU
    except Exception as e:
        logger.error(f"Error processing name input: {e}")
        await update.message.reply_text("oops! something went wrong. let's start over with /start 😅")
        return MENU

async def confirm_role_and_name(query, role: str, name: str) -> int:
    """
    Confirm and save the user's role and name.
    
    Args:
        query: Telegram callback query object
        role: Selected role ('boyfriend' or 'girlfriend')
        name: User's name
        
    Returns:
        int: MENU to return to main menu after setting role and name
    """
    try:
        user_id = query.from_user.id
        role_success = set_user_role(user_id, role)
        name_success = set_user_name(user_id, name)
        
        if role_success and name_success:
            emoji = "💙" if role == "boyfriend" else "💖"
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text=f"✅ sup **{name}**! {emoji}\n\n"
                     f"okay la ur the **{role}** la\n\n"
                     f"💕 you can now submit content for your partner and access role-specific features. yippee!",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        else:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="❌ cannot sia u try again",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error in confirm_role_and_name: {e}")
        return await show_main_menu_from_query(query)

# Content submission handlers
async def handle_submit_photo(query) -> int:
    """
    Handle photo submission button click.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: WAITING_PHOTO_UPLOAD state
    """
    try:
        user_role = get_user_role(query.from_user.id)
        if not user_role:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="⚠️ please set your role first! 💕",
                reply_markup=reply_markup
            )
            return MENU
        
        partner_role = "girlfriend" if user_role == "boyfriend" else "boyfriend"
        
        await query.edit_message_text(
            text=f"📸 **submit a photo for your {partner_role}!**\n\n"
                 "send me a photo and i'll add it to their collection! 💕\n\n"
                 "_(type /cancel to go back to menu)_",
            parse_mode='Markdown'
        )
        return WAITING_PHOTO_UPLOAD
    except Exception as e:
        logger.error(f"Error in handle_submit_photo: {e}")
        return await show_main_menu_from_query(query)

async def handle_submit_bubble(query) -> int:
    """
    Handle video bubble submission button click.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: WAITING_VIDEO_UPLOAD state
    """
    try:
        user_role = get_user_role(query.from_user.id)
        if not user_role:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="⚠️ please set your role first! 💕",
                reply_markup=reply_markup
            )
            return MENU
        
        partner_role = "girlfriend" if user_role == "boyfriend" else "boyfriend"
        
        await query.edit_message_text(
            text=f"🫧 **submit a video bubble for your {partner_role}!** \n\n"
                 "send me a video and i'll add it to their bubble collection! 💕\n\n"
                 " _(type /cancel to go back to menu)_ ",
            parse_mode='Markdown'
        )
        return WAITING_VIDEO_UPLOAD
    except Exception as e:
        logger.error(f"Error in handle_submit_bubble: {e}")
        return await show_main_menu_from_query(query)

async def process_photo_upload(update: Update, context: CallbackContext) -> int:
    """
    Process uploaded photo for partner.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: MENU to return to main menu
    """
    try:
        user_role = get_user_role(update.effective_user.id)
        if not user_role:
            await update.message.reply_text("⚠️ error: role not found. please set your role first! 💕")
            return MENU
        
        # Get the photo
        photo = update.message.photo[-1]  # Get the highest resolution
        file = await context.bot.get_file(photo.file_id)
        
        # Create directories if they don't exist
        script_dir = os.path.dirname(os.path.abspath(__file__))
        partner_role = "girlfriend" if user_role == "boyfriend" else "boyfriend"
        images_dir = os.path.join(script_dir, "images", partner_role)
        os.makedirs(images_dir, exist_ok=True)
        
        # Save the photo
        import time
        filename = f"submitted_{int(time.time())}_{photo.file_id[:8]}.jpg"
        file_path = os.path.join(images_dir, filename)
        await file.download_to_drive(file_path)
        
        # Add to partner's content
        relative_path = f"images/{partner_role}/{filename}"
        success = save_content_for_partner('image_paths', relative_path, user_role)
        
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if success:
            await update.message.reply_text(
                f"✅ **photo submitted successfully!** 📸\n\n"
                f"your {partner_role} will now see this photo when they click 'i wanna see you'! 💕",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ failed to save photo. please try again! 😅",
                reply_markup=reply_markup
            )
        
    except Exception as e:
        logger.error(f"Error processing photo upload: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "oops! something went wrong while uploading your photo 📸💔",
            reply_markup=reply_markup
        )
    
    return MENU

async def process_video_upload(update: Update, context: CallbackContext) -> int:
    """
    Process uploaded video for partner's bubble collection.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: MENU to return to main menu
    """
    try:
        user_role = get_user_role(update.effective_user.id)
        if not user_role:
            await update.message.reply_text("⚠️ error: role not found. please set your role first! 💕")
            return MENU
        
        # Get the video
        video = update.message.video
        if not video:
            # Try video note (circular videos)
            video = update.message.video_note
        
        if not video:
            await update.message.reply_text("⚠️ please send a video file! 📹")
            return MENU
        
        file = await context.bot.get_file(video.file_id)
        
        # Create directories if they don't exist
        script_dir = os.path.dirname(os.path.abspath(__file__))
        partner_role = "girlfriend" if user_role == "boyfriend" else "boyfriend"
        videos_dir = os.path.join(script_dir, "videos", partner_role)
        os.makedirs(videos_dir, exist_ok=True)
        
        # Save the video
        import time
        filename = f"bubble_{int(time.time())}_{video.file_id[:8]}.mp4"
        file_path = os.path.join(videos_dir, filename)
        await file.download_to_drive(file_path)
        
        # Add to partner's content
        relative_path = f"videos/{partner_role}/{filename}"
        success = save_content_for_partner('video_messages', relative_path, user_role)
        
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if success:
            await update.message.reply_text(
                f"✅ **video bubble submitted successfully!** 🫧\n\n"
                f"your {partner_role} will now see this video when they want a bubble! 💕",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ failed to save video bubble. please try again! 😅",
                reply_markup=reply_markup
            )
        
    except Exception as e:
        logger.error(f"Error processing video upload: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "oops! something went wrong while uploading your video bubble 🫧💔",
            reply_markup=reply_markup
        )
    
    return MENU

async def process_text(update: Update, context: CallbackContext) -> int:
    """
    Process text input from user.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: MENU to return to main menu
    """
    logger.info(f"Received text input: {update.message.text}")
    try:
        text = update.message.text.strip()
        await update.message.reply_text(f"{text}? okay buddy... /start to chat bro... 😎")
        
    except Exception as e:
        logger.error(f"Error processing text input: {e}")
        await update.message.reply_text("sorry something broke... 😅")
    
    return MENU

# Start command handler
async def start(update: Update, context: CallbackContext) -> int:
    """
    Handle /start command and display the main menu with all available options.
    Creates an inline keyboard with buttons for all bot features.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: MENU state to handle button presses
    """
    user_id = update.effective_user.id
    user_role = get_user_role(user_id)
    user_name = get_user_name(user_id)
    
    # Base menu options
    keyboard = [
        [InlineKeyboardButton("💕 gimme some rizz", callback_data="flirt")],
        [InlineKeyboardButton("📸 i wanna see you", callback_data="picture")],
        [InlineKeyboardButton("🫧 i want a bubble", callback_data="bubble")],
        [InlineKeyboardButton("💪 i need motivation", callback_data="motivation")],
        [InlineKeyboardButton("📊 show me our stats", callback_data="stats")],
        [InlineKeyboardButton("⏰ set a reminder", callback_data="reminder")],
        [InlineKeyboardButton("🍽️ where should we eat?", callback_data="restaurant")]
    ]
    
    # Add role-specific submission options
    if user_role:
        keyboard.extend([
            [InlineKeyboardButton("📤 submit photo for partner", callback_data="submit_photo")],
            [InlineKeyboardButton("🫧 submit bubble for partner", callback_data="submit_bubble")],
        ])
    
    # Role management and exit options
    if not user_role:
        keyboard.extend([
            [InlineKeyboardButton("👤 set my role", callback_data="set_role")],
            [InlineKeyboardButton("❌ exit bot", callback_data="exit")]
        ])
    else:
        keyboard.extend([
            [InlineKeyboardButton(f"👤 role: {user_role}", callback_data="change_role")],
            [InlineKeyboardButton("❌ exit bot", callback_data="exit")]
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if user_role:
        name_display = f" {user_name}" if user_name else ""
        welcome_message = (
            f"💕 **hi {user_role}{name_display} :P, welcome back!!** 💕\n"
            "i'm here to make your day brighter with:\n"
            "• flirty messages 💕\n" 
            "• pictures from your partner 📸\n"
            "• motivational pep talks 💪\n"
            "• bubbles from your partner 🫧\n"
            "• relationship stats 📊\n"
            "• reminders ⏰\n"
            "• restaurant suggestions 🍽️\n\n"
            "**plus, you can now submit content for your partner!** ✨\n\n"
            "**choose what you need right now! ✨**\n"
            "_(i'll keep running until you type /stop or click exit)_ 💕"
        )
    else:
        welcome_message = (
            "💕 **welcome to your personal relationship bot!** 💕\n\n"
            "⚠️ **first, please set your role!** ⚠️\n"
            "are you the boyfriend or girlfriend? this determines:\n"
            "• what pictures you'll see 📸\n"
            "• what bubbles you'll receive 🫧\n"
            "• what content you can submit 📤\n\n"
            "click '👤 set my role' to get started! 💕\n\n"
            "**basic features available:**\n"
            "• flirty messages 💕\n" 
            "• motivational pep talks 💪\n"
            "• relationship stats 📊\n"
            "• reminders ⏰\n"
            "• restaurant suggestions 🍽️\n\n"
            "_(i'll keep running until you type /stop or click exit)_ ✨"
        )
    
    await update.message.reply_text(
        welcome_message, 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MENU

# Button click handler
async def button(update: Update, context: CallbackContext) -> int:
    """
    Handle button clicks from the inline keyboard.
    Routes to appropriate handler functions based on callback data.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: Appropriate conversation state based on selected option
    """
    query = update.callback_query
    await query.answer()
    
    if query.data == "flirt":
        return await handle_flirt(query)
    elif query.data == "picture":
        return await handle_picture(query)
    elif query.data == "bubble":
        return await handle_bubble(query)
    elif query.data == "motivation":
        return await handle_motivation(query)
    elif query.data == "stats":
        return await handle_stats(query)
    elif query.data == "reminder":
        return await handle_reminder(query)
    elif query.data == "restaurant":
        return await handle_restaurant(query)
    elif query.data == "set_role" or query.data == "change_role":
        return await handle_set_role(query)
    elif query.data == "role_boyfriend":
        return await handle_role_selection(query, "boyfriend")
    elif query.data == "role_girlfriend":
        return await handle_role_selection(query, "girlfriend")
    elif query.data.startswith("confirm_boyfriend_"):
        name = query.data.replace("confirm_boyfriend_", "")
        return await confirm_role_and_name(query, "boyfriend", name)
    elif query.data.startswith("confirm_girlfriend_"):
        name = query.data.replace("confirm_girlfriend_", "")
        return await confirm_role_and_name(query, "girlfriend", name)
    elif query.data == "submit_photo":
        return await handle_submit_photo(query)
    elif query.data == "submit_bubble":
        return await handle_submit_bubble(query)
    elif query.data == "back_to_menu":
        return await show_main_menu_from_query(query)
    elif query.data == "exit":
        await query.edit_message_text(text="goodbye love! thanks for letting me brighten your day 💕✨\n\ntype /start anytime to chat again!")
        return ConversationHandler.END
    else:
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="unknown option selected. let's try again! 🔄",
            reply_markup=reply_markup
        )
        return MENU

# Stop command handler
async def stop(update: Update, context: CallbackContext) -> int:
    """
    Handle /stop command to end the bot session.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: ConversationHandler.END to end conversation
    """
    await update.message.reply_text("goodbye love! thanks for letting me brighten your day 💕✨\n\ntype /start anytime to chat again!")
    return ConversationHandler.END

# Cancel handler
async def cancel(update: Update, context: CallbackContext) -> int:
    """
    Handle /cancel command to return to main menu or end conversation.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: MENU to return to main menu
    """
    user_id = update.effective_user.id
    user_role = get_user_role(user_id)
    
    # Base menu options
    keyboard = [
        [InlineKeyboardButton("💕 gimme some rizz", callback_data="flirt")],
        [InlineKeyboardButton("📸 i wanna see you", callback_data="picture")],
        [InlineKeyboardButton("🫧 i want a bubble", callback_data="bubble")],
        [InlineKeyboardButton("💪 i need motivation", callback_data="motivation")],
        [InlineKeyboardButton("📊 show me our stats", callback_data="stats")],
        [InlineKeyboardButton("⏰ set a reminder", callback_data="reminder")],
        [InlineKeyboardButton("🍽️ where should we eat?", callback_data="restaurant")]
    ]
    
    # Add role-specific submission options
    if user_role:
        keyboard.extend([
            [InlineKeyboardButton("📤 submit photo for partner", callback_data="submit_photo")],
            [InlineKeyboardButton("🫧 submit bubble for partner", callback_data="submit_bubble")]
        ])
    
    # Role management and exit options
    if not user_role:
        keyboard.extend([
            [InlineKeyboardButton("👤 set my role", callback_data="set_role")],
            [InlineKeyboardButton("❌ exit bot", callback_data="exit")]
        ])
    else:
        keyboard.extend([
            [InlineKeyboardButton(f"👤 role: {user_role}", callback_data="change_role")],
            [InlineKeyboardButton("❌ exit bot", callback_data="exit")]
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if user_role:
        message_text = f"💫 **back to the main menu!** 💫\nrole: **{user_role}** 👤\n\nwhat would you like to do next? ✨"
    else:
        message_text = "💫 **back to the main menu!** 💫\n⚠️ please set your role first to access all features! 💕\n\nwhat would you like to do? ✨"
    
    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MENU

# Main function to start the bot
def main():
    """
    Main function to initialize and start the Telegram bot.
    Sets up conversation handlers and starts polling for updates.
    """
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
            MENU: [
                CallbackQueryHandler(button),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_text)
            ],
            WAITING_REMINDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_reminder_text)],
            WAITING_REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_reminder_time)],
            WAITING_PHOTO_UPLOAD: [MessageHandler(filters.PHOTO, process_photo_upload)],
            WAITING_VIDEO_UPLOAD: [MessageHandler(filters.VIDEO | filters.VIDEO_NOTE, process_video_upload)],
            WAITING_NAME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_name_input)],
            DEFAULT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_text)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("stop", stop),
            CommandHandler("exit", stop),
            CommandHandler("start", start)
        ],
    )

    application.add_handler(conv_handler)
    
    logger.info("Bot started successfully! 🤖💕")
    logger.info("Bot will keep running and return to menu after each action")
    logger.info("Users can type /stop, /exit, /cancel, or click 'exit bot' to quit")
    logger.info("Role-based system enabled - users can be 'boyfriend' or 'girlfriend'")
    logger.info("Content submission enabled - partners can submit photos and bubbles for each other")
    application.run_polling()

if __name__ == "__main__":
    main()