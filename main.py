import logging
import os
import json
import random
import datetime
import asyncio
import threading
import pytz
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
MENU, WAITING_REMINDER_TEXT, WAITING_REMINDER_TIME, WAITING_PHOTO_UPLOAD, WAITING_BUBBLE_TEXT, WAITING_VIDEO_UPLOAD, WAITING_NAME_INPUT, WAITING_DAILY_REMINDER_TEXT, WAITING_DAILY_REMINDER_TIME, WAITING_PARTNER_REMINDER_TEXT, WAITING_PARTNER_REMINDER_TIME, DEFAULT = range(12)

# Set up logging for the bot
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Timezone configuration
TIMEZONES = {
    'boyfriend': 'America/New_York',  # New Orleans is in Central Time, but using Eastern for now
    'girlfriend': 'Europe/Prague'
}

# Actually, let's use the correct timezone for New Orleans
TIMEZONES = {
    'boyfriend': 'America/Chicago',  # New Orleans is in Central Time
    'girlfriend': 'Europe/Prague'
}

def get_current_times():
    """
    Get current times in both Prague and New Orleans.
    
    Returns:
        dict: Dictionary with formatted time strings for both locations
    """
    try:
        prague_tz = pytz.timezone(TIMEZONES['girlfriend'])
        new_orleans_tz = pytz.timezone(TIMEZONES['boyfriend'])
        
        utc_now = datetime.datetime.now(pytz.UTC)
        
        prague_time = utc_now.astimezone(prague_tz)
        new_orleans_time = utc_now.astimezone(new_orleans_tz)
        
        return {
            'prague': {
                'time': prague_time.strftime("%I:%M %p"),
                'date': prague_time.strftime("%B %d"),
                'full': prague_time.strftime("%I:%M %p, %B %d")
            },
            'new_orleans': {
                'time': new_orleans_time.strftime("%I:%M %p"), 
                'date': new_orleans_time.strftime("%B %d"),
                'full': new_orleans_time.strftime("%I:%M %p, %B %d")
            }
        }
    except Exception as e:
        logger.error(f"Error getting current times: {e}")
        return {
            'prague': {'time': 'N/A', 'date': 'N/A', 'full': 'N/A'},
            'new_orleans': {'time': 'N/A', 'date': 'N/A', 'full': 'N/A'}
        }

def get_user_timezone(user_role: str) -> str:
    """
    Get timezone for user based on their role.
    
    Args:
        user_role (str): User role ('boyfriend' or 'girlfriend')
        
    Returns:
        str: Timezone string
    """
    return TIMEZONES.get(user_role, 'UTC')

def format_time_with_both_zones(base_time: str, context: str = "") -> str:
    """
    Format time display showing both Prague and New Orleans times.
    
    Args:
        base_time (str): Base time string
        context (str): Context for the time display
        
    Returns:
        str: Formatted string with both timezone times
    """
    times = get_current_times()
    
    time_display = f"🕐 **current times** 🕐\n"
    time_display += f"🇨🇿 **prague:** {times['prague']['full']}\n"  
    time_display += f"🇺🇸 **new orleans:** {times['new_orleans']['full']}"
    
    if context:
        time_display = f"{context}\n\n{time_display}"
    
    return time_display

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

def get_user_daily_reminders(user_id: int) -> list:
    """
    Get daily reminders for a specific user.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        list: List of daily reminders for the user
    """
    try:
        data = load_json_data('bot_data.json')
        daily_reminders = data.get('daily_reminders', {})
        return daily_reminders.get(str(user_id), [])
    except Exception as e:
        logger.error(f"Error getting daily reminders: {e}")
        return []

def get_user_one_time_reminders(user_id: int) -> list:
    """
    Get one-time reminders for a specific user.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        list: List of one-time reminders for the user
    """
    try:
        data = load_json_data('bot_data.json')
        one_time_reminders = data.get('one_time_reminders', {})
        return one_time_reminders.get(str(user_id), [])
    except Exception as e:
        logger.error(f"Error getting one-time reminders: {e}")
        return []

def save_one_time_reminder(user_id: int, reminder_text: str, reminder_datetime: str) -> bool:
    """
    Save a one-time reminder for a user.
    
    Args:
        user_id (int): Telegram user ID
        reminder_text (str): The reminder message
        reminder_datetime (str): DateTime in ISO format
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = load_json_data('bot_data.json')
        
        if 'one_time_reminders' not in data:
            data['one_time_reminders'] = {}
        
        if str(user_id) not in data['one_time_reminders']:
            data['one_time_reminders'][str(user_id)] = []
        
        # Add the new reminder
        reminder = {
            'text': reminder_text,
            'datetime': reminder_datetime,
            'sent': False,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        data['one_time_reminders'][str(user_id)].append(reminder)
        return save_json_data('bot_data.json', data)
        
    except Exception as e:
        logger.error(f"Error saving one-time reminder: {e}")
        return False

def mark_reminder_sent(user_id: int, reminder_index: int) -> bool:
    """
    Mark a one-time reminder as sent.
    
    Args:
        user_id (int): Telegram user ID
        reminder_index (int): Index of the reminder to mark as sent
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = load_json_data('bot_data.json')
        
        if 'one_time_reminders' not in data or str(user_id) not in data['one_time_reminders']:
            return False
        
        reminders = data['one_time_reminders'][str(user_id)]
        if 0 <= reminder_index < len(reminders):
            reminders[reminder_index]['sent'] = True
            return save_json_data('bot_data.json', data)
        
        return False
        
    except Exception as e:
        logger.error(f"Error marking reminder as sent: {e}")
        return False

def get_partner_user_id(user_id: int) -> Optional[int]:
    """
    Get the partner's user ID based on roles.
    
    Args:
        user_id (int): Current user's Telegram ID
        
    Returns:
        Optional[int]: Partner's user ID or None if not found
    """
    try:
        data = load_json_data('bot_data.json')
        user_roles = data.get('user_roles', {})
        current_role = user_roles.get(str(user_id))
        
        if not current_role:
            return None
        
        # Find partner with opposite role
        partner_role = 'girlfriend' if current_role == 'boyfriend' else 'boyfriend'
        
        for uid, role in user_roles.items():
            if role == partner_role and int(uid) != user_id:
                return int(uid)
        
        return None
    except Exception as e:
        logger.error(f"Error getting partner user ID: {e}")
        return None

def save_partner_reminder(sender_id: int, partner_id: int, reminder_text: str, reminder_datetime: str) -> bool:
    """
    Save a reminder from one partner to another.
    
    Args:
        sender_id (int): User ID who is setting the reminder
        partner_id (int): Partner's user ID who will receive the reminder
        reminder_text (str): The reminder message
        reminder_datetime (str): DateTime in ISO format
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = load_json_data('bot_data.json')
        
        if 'partner_reminders' not in data:
            data['partner_reminders'] = {}
        
        if str(partner_id) not in data['partner_reminders']:
            data['partner_reminders'][str(partner_id)] = []
        
        # Get sender's name
        sender_name = get_user_name(sender_id) or "your partner"
        
        # Add the new partner reminder
        reminder = {
            'text': reminder_text,
            'datetime': reminder_datetime,
            'sent': False,
            'sender_id': sender_id,
            'sender_name': sender_name,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        data['partner_reminders'][str(partner_id)].append(reminder)
        return save_json_data('bot_data.json', data)
        
    except Exception as e:
        logger.error(f"Error saving partner reminder: {e}")
        return False

def get_user_partner_reminders(user_id: int) -> list:
    """
    Get partner reminders for a specific user.
    
    Args:
        user_id (int): Telegram user ID
        
    Returns:
        list: List of partner reminders for the user
    """
    try:
        data = load_json_data('bot_data.json')
        partner_reminders = data.get('partner_reminders', {})
        return partner_reminders.get(str(user_id), [])
    except Exception as e:
        logger.error(f"Error getting partner reminders: {e}")
        return []

def mark_partner_reminder_sent(user_id: int, reminder_index: int) -> bool:
    """
    Mark a partner reminder as sent.
    
    Args:
        user_id (int): Telegram user ID
        reminder_index (int): Index of the reminder to mark as sent
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = load_json_data('bot_data.json')
        
        if 'partner_reminders' not in data or str(user_id) not in data['partner_reminders']:
            return False
        
        reminders = data['partner_reminders'][str(user_id)]
        if 0 <= reminder_index < len(reminders):
            reminders[reminder_index]['sent'] = True
            return save_json_data('bot_data.json', data)
        
        return False
        
    except Exception as e:
        logger.error(f"Error marking partner reminder as sent: {e}")
        return False

def save_daily_reminder(user_id: int, reminder_text: str, reminder_time: str) -> bool:
    """
    Save a daily reminder for a user.
    
    Args:
        user_id (int): Telegram user ID
        reminder_text (str): The reminder message
        reminder_time (str): Time in HH:MM format
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = load_json_data('bot_data.json')
        
        if 'daily_reminders' not in data:
            data['daily_reminders'] = {}
        
        if str(user_id) not in data['daily_reminders']:
            data['daily_reminders'][str(user_id)] = []
        
        # Add the new reminder
        reminder = {
            'text': reminder_text,
            'time': reminder_time,
            'active': True,
            'created_at': datetime.datetime.now().isoformat()
        }
        
        data['daily_reminders'][str(user_id)].append(reminder)
        return save_json_data('bot_data.json', data)
        
    except Exception as e:
        logger.error(f"Error saving daily reminder: {e}")
        return False

def remove_daily_reminder(user_id: int, reminder_index: int) -> bool:
    """
    Remove a daily reminder for a user.
    
    Args:
        user_id (int): Telegram user ID
        reminder_index (int): Index of the reminder to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = load_json_data('bot_data.json')
        
        if 'daily_reminders' not in data or str(user_id) not in data['daily_reminders']:
            return False
        
        reminders = data['daily_reminders'][str(user_id)]
        if 0 <= reminder_index < len(reminders):
            reminders.pop(reminder_index)
            return save_json_data('bot_data.json', data)
        
        return False
        
    except Exception as e:
        logger.error(f"Error removing daily reminder: {e}")
        return False

def toggle_daily_reminder(user_id: int, reminder_index: int) -> bool:
    """
    Toggle a daily reminder active/inactive status.
    
    Args:
        user_id (int): Telegram user ID
        reminder_index (int): Index of the reminder to toggle
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        data = load_json_data('bot_data.json')
        
        if 'daily_reminders' not in data or str(user_id) not in data['daily_reminders']:
            return False
        
        reminders = data['daily_reminders'][str(user_id)]
        if 0 <= reminder_index < len(reminders):
            reminders[reminder_index]['active'] = not reminders[reminder_index].get('active', True)
            return save_json_data('bot_data.json', data)
        
        return False
        
    except Exception as e:
        logger.error(f"Error toggling daily reminder: {e}")
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

class DailyReminderScheduler:
    """
    Class to handle daily reminder scheduling and sending.
    """
    
    def __init__(self, application):
        self.application = application
        self.running = False
        self.scheduler_thread = None
        self.loop = None
    
    def start(self):
        """Start the daily reminder scheduler."""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            logger.info("Daily reminder scheduler started! 📅")
    
    def stop(self):
        """Stop the daily reminder scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("Daily reminder scheduler stopped! 📅")
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        # Create a new event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        while self.running:
            try:
                self.loop.run_until_complete(self._check_and_send_reminders())
                # Check every minute
                threading.Event().wait(60)
            except Exception as e:
                logger.error(f"Error in reminder scheduler: {e}")
                threading.Event().wait(60)
        
        # Clean up the loop
        self.loop.close()
    
    async def _check_and_send_reminders(self):
        """Check if any reminders need to be sent now."""
        try:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            current_datetime = now
            
            data = load_json_data('bot_data.json')
            
            # Check daily reminders
            daily_reminders = data.get('daily_reminders', {})
            for user_id, reminders in daily_reminders.items():
                for reminder in reminders:
                    if (reminder.get('active', True) and 
                        reminder.get('time') == current_time):
                        
                        # Send the daily reminder
                        await self._send_daily_reminder(int(user_id), reminder['text'])
            
            # Check one-time reminders
            one_time_reminders = data.get('one_time_reminders', {})
            for user_id, reminders in one_time_reminders.items():
                for i, reminder in enumerate(reminders):
                    if not reminder.get('sent', False):
                        try:
                            reminder_datetime = datetime.datetime.fromisoformat(reminder['datetime'])
                            # Check if reminder time has passed (within 1 minute window)
                            if (current_datetime >= reminder_datetime and 
                                (current_datetime - reminder_datetime).total_seconds() < 60):
                                
                                # Send the one-time reminder
                                await self._send_one_time_reminder(int(user_id), reminder['text'])
                                # Mark as sent
                                mark_reminder_sent(int(user_id), i)
                        except ValueError:
                            logger.error(f"Invalid datetime format in reminder: {reminder['datetime']}")
            
            # Check partner reminders
            partner_reminders = data.get('partner_reminders', {})
            for user_id, reminders in partner_reminders.items():
                for i, reminder in enumerate(reminders):
                    if not reminder.get('sent', False):
                        try:
                            reminder_datetime = datetime.datetime.fromisoformat(reminder['datetime'])
                            # Check if reminder time has passed (within 1 minute window)
                            if (current_datetime >= reminder_datetime and 
                                (current_datetime - reminder_datetime).total_seconds() < 60):
                                
                                # Send the partner reminder
                                await self._send_partner_reminder(
                                    int(user_id), 
                                    reminder['text'], 
                                    reminder.get('sender_name', 'your partner')
                                )
                                # Mark as sent
                                mark_partner_reminder_sent(int(user_id), i)
                        except ValueError:
                            logger.error(f"Invalid datetime format in partner reminder: {reminder['datetime']}")
                            
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
    
    async def _send_daily_reminder(self, user_id: int, reminder_text: str):
        """Send a daily reminder to a user."""
        try:
            user_name = get_user_name(user_id)
            name_part = f" {user_name}" if user_name else ""
            
            message = f"⏰ **daily reminder!** ⏰\n\n💕 hey{name_part}! 💕\n\n📝 {reminder_text}\n\n✨ have a great day! ✨"
            
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"Daily reminder sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending daily reminder to user {user_id}: {e}")
    
    async def _send_one_time_reminder(self, user_id: int, reminder_text: str):
        """Send a one-time reminder to a user."""
        try:
            user_name = get_user_name(user_id)
            name_part = f" {user_name}" if user_name else ""
            
            message = f"🔔 **reminder time!** 🔔\n\n💕 hey{name_part}! 💕\n\n📝 {reminder_text}\n\n✨ hope this helps! ✨"
            
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"One-time reminder sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending one-time reminder to user {user_id}: {e}")
    
    async def _send_partner_reminder(self, user_id: int, reminder_text: str, sender_name: str):
        """Send a partner reminder to a user."""
        try:
            user_name = get_user_name(user_id)
            name_part = f" {user_name}" if user_name else ""
            
            # Get current times for both locations
            times = get_current_times()
            time_info = f"\n\n🕐 **current times** 🕐\n🇨🇿 **prague:** {times['prague']['full']}\n🇺🇸 **new orleans:** {times['new_orleans']['full']}"
            
            message = f"💌 **reminder from {sender_name}!** 💌\n\n💕 hey{name_part}! 💕\n\n📝 {sender_name} wanted to remind you: {reminder_text}\n\n✨ they're thinking of you! ✨{time_info}"
            
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"Partner reminder sent to user {user_id} from {sender_name}")
            
        except Exception as e:
            logger.error(f"Error sending partner reminder to user {user_id}: {e}")

# Global scheduler instance
reminder_scheduler = None

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
        [InlineKeyboardButton("💕 gimme some rizz", callback_data="flirt")],
        [InlineKeyboardButton("📸 i wanna see you", callback_data="picture")],
        [InlineKeyboardButton("🫧 i want a bubble", callback_data="bubble")],
        [InlineKeyboardButton("💪 i need motivation", callback_data="motivation")],
        [InlineKeyboardButton("📊 show me our stats", callback_data="stats")],
        [InlineKeyboardButton("⏰ set a reminder", callback_data="reminder")],
        [InlineKeyboardButton("📅 daily reminders", callback_data="daily_reminders")]
    ]
    
    # Add role-specific submission options and partner reminders
    if user_role:
        keyboard.extend([
            [InlineKeyboardButton("📤 submit photo for partner", callback_data="submit_photo")],
            [InlineKeyboardButton("🫧 submit bubble for partner", callback_data="submit_bubble")],
            [InlineKeyboardButton("💌 set reminder for partner", callback_data="partner_reminder")]
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
    
    # Get current times for both locations
    times = get_current_times()
    time_info = f"\n\n🕐 **current times** 🕐\n🇨🇿 **prague:** {times['prague']['full']}\n🇺🇸 **new orleans:** {times['new_orleans']['full']}"
    
    if user_role:
        back_message = (
            f"💫 **back to the main menu!** 💫\n"
            f"role: **{user_role}** 👤\n\n"
            "what would you like to do next? ✨"
            f"{time_info}"
        )
    else:
        back_message = (
            "💫 **welcome to the main menu!** 💫\n"
            "⚠️ please set your role first to access all features! 💕\n\n"
            "what would you like to do? ✨"
            f"{time_info}"
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
                text="**sorry, i'm feeling a bit tongue-tied right now!** 😅",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return MENU
        
        flirt_messages = data['flirt_messages']
        random_flirt = random.choice(flirt_messages)
        
        # Create inline keyboard with back to menu option
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"💕 {random_flirt}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in handle_flirt: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="**oops!** something went wrong with my rizz game... L rizz 😬",
            reply_markup=reply_markup,
            parse_mode='Markdown'
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
        await update.message.reply_text("oops! something went wrong. let's start over with /start", parse_mode='Markdown')
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
        time_input = update.message.text.lower().strip()
        reminder_text = context.user_data.get('reminder_text', 'generic reminder')
        user_id = update.effective_user.id
        
        # Create back to menu keyboard
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if time_input == "now":
            # Send immediate reminder
            user_name = get_user_name(user_id)
            name_part = f" {user_name}" if user_name else ""
            await update.message.reply_text(
                f"🔔 **reminder right now!** 🔔\n\n💕 hey{name_part}! 💕\n\n📝 {reminder_text}\n\n✨ here's your reminder! ✨", 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        elif time_input == "tomorrow":
            # Schedule for same time tomorrow
            now = datetime.datetime.now()
            tomorrow = now + datetime.timedelta(days=1)
            reminder_datetime = tomorrow.replace(second=0, microsecond=0)
            
            success = save_one_time_reminder(user_id, reminder_text, reminder_datetime.isoformat())
            
            if success:
                await update.message.reply_text(
                    f"✅ **reminder scheduled for tomorrow!** 📅\n\n"
                    f"⏰ **time:** {reminder_datetime.strftime('%B %d, %Y at %I:%M %p')}\n"
                    f"📝 **message:** \"{reminder_text}\"\n\n"
                    f"i'll send you this reminder tomorrow! ✨",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ failed to schedule reminder. please try again! �",
                    reply_markup=reply_markup
                )
        elif ":" in time_input:
            # Parse time format HH:MM
            try:
                time_obj = datetime.datetime.strptime(time_input, "%H:%M")
                now = datetime.datetime.now()
                
                # Schedule for today if time hasn't passed, otherwise tomorrow
                reminder_datetime = now.replace(
                    hour=time_obj.hour, 
                    minute=time_obj.minute, 
                    second=0, 
                    microsecond=0
                )
                
                if reminder_datetime <= now:
                    # Time has passed today, schedule for tomorrow
                    reminder_datetime += datetime.timedelta(days=1)
                
                success = save_one_time_reminder(user_id, reminder_text, reminder_datetime.isoformat())
                
                if success:
                    display_time = reminder_datetime.strftime("%I:%M %p").lstrip('0')
                    day_text = "today" if reminder_datetime.date() == now.date() else "tomorrow"
                    
                    await update.message.reply_text(
                        f"✅ **reminder scheduled!** ⏰\n\n"
                        f"⏰ **time:** {day_text} at {display_time}\n"
                        f"📝 **message:** \"{reminder_text}\"\n\n"
                        f"i'll send you this reminder {day_text}! ✨",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "❌ failed to schedule reminder. please try again! 😅",
                        reply_markup=reply_markup
                    )
                    
            except ValueError:
                await update.message.reply_text(
                    "❌ **invalid time format!** ⏰\n\n"
                    "please use **HH:MM** format (24-hour):\n"
                    "• **09:00** ✅\n"
                    "• **14:30** ✅\n"
                    "• **9:00** ❌ (use 09:00)\n"
                    "• **2:30 PM** ❌ (use 14:30)\n\n"
                    "or use:\n"
                    "• **now** for immediate reminder ⚡\n"
                    "• **tomorrow** for same time tomorrow 📅\n\n"
                    "try again! �",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return WAITING_REMINDER_TIME
        else:
            await update.message.reply_text(
                f"❌ **couldn't understand time format!** 😅\n\n"
                f"please try:\n"
                f"• **HH:MM** format (e.g., 14:30) ⏰\n"
                f"• **now** for immediate reminder ⚡\n"
                f"• **tomorrow** for same time tomorrow 📅\n\n"
                f"your reminder \"{reminder_text}\" is waiting! 💕",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return WAITING_REMINDER_TIME
        
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

# Daily reminder handlers
async def handle_daily_reminders(query) -> int:
    """
    Handle daily reminders button click and show reminder management menu.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: MENU state
    """
    try:
        user_id = query.from_user.id
        reminders = get_user_daily_reminders(user_id)
        
        keyboard = [
            [InlineKeyboardButton("➕ add new daily reminder", callback_data="add_daily_reminder")]
        ]
        
        message = "📅 **daily reminders management** 📅\n\n"
        
        if reminders:
            message += "**your current daily reminders:**\n\n"
            for i, reminder in enumerate(reminders):
                status = "✅" if reminder.get('active', True) else "❌"
                message += f"{i+1}. {status} **{reminder['time']}** - {reminder['text']}\n"
            
            message += "\n**manage your reminders:**\n"
            
            # Add management buttons
            for i, reminder in enumerate(reminders):
                status_text = "disable" if reminder.get('active', True) else "enable"
                keyboard.append([
                    InlineKeyboardButton(f"🔄 {status_text} #{i+1}", callback_data=f"toggle_reminder_{i}"),
                    InlineKeyboardButton(f"🗑️ delete #{i+1}", callback_data=f"delete_reminder_{i}")
                ])
            
        else:
            message += "you have no daily reminders set up yet! 😊\n\n"
            message += "daily reminders will send you a message every day at the time you choose! ⏰\n\n"
        
        keyboard.append([InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in handle_daily_reminders: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="oops! something went wrong with daily reminders 😅",
            reply_markup=reply_markup
        )
    
    return MENU

async def handle_add_daily_reminder(query) -> int:
    """
    Handle adding a new daily reminder.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: WAITING_DAILY_REMINDER_TEXT state
    """
    try:
        await query.edit_message_text(
            text="📅 **create a new daily reminder!** 📅\n\n"
                 "💬 what would you like to be reminded about daily?\n"
                 "just type your reminder message! ✨\n\n"
                 "examples:\n"
                 "• drink water! 💧\n"
                 "• call your partner 💕\n"
                 "• take your vitamins 💊\n"
                 "• you're amazing! 🌟\n\n"
                 "_(type /cancel to go back to menu)_",
            parse_mode='Markdown'
        )
        return WAITING_DAILY_REMINDER_TEXT
    except Exception as e:
        logger.error(f"Error in handle_add_daily_reminder: {e}")
        return await show_main_menu_from_query(query)

async def process_daily_reminder_text(update: Update, context: CallbackContext) -> int:
    """
    Process the daily reminder text input from user.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: WAITING_DAILY_REMINDER_TIME state
    """
    try:
        reminder_text = update.message.text.strip()
        context.user_data['daily_reminder_text'] = reminder_text
        
        await update.message.reply_text(
            f"📝 **daily reminder text:** \"{reminder_text}\" ✨\n\n"
            "⏰ **what time should i send this reminder daily?**\n\n"
            "please send the time in **HH:MM** format (24-hour):\n"
            "• **08:00** for 8:00 AM 🌅\n"
            "• **12:00** for 12:00 PM (noon) ☀️\n"
            "• **18:30** for 6:30 PM 🌆\n"
            "• **22:00** for 10:00 PM 🌙\n\n"
            "_(type /cancel to go back to menu)_",
            parse_mode='Markdown'
        )
        return WAITING_DAILY_REMINDER_TIME
    except Exception as e:
        logger.error(f"Error processing daily reminder text: {e}")
        await update.message.reply_text("oops! something went wrong. let's start over with /start 😅", parse_mode='Markdown')
        return MENU

async def process_daily_reminder_time(update: Update, context: CallbackContext) -> int:
    """
    Process the daily reminder time input and save the reminder.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: MENU state
    """
    try:
        time_input = update.message.text.strip()
        reminder_text = context.user_data.get('daily_reminder_text', 'daily reminder')
        user_id = update.effective_user.id
        
        # Validate time format
        try:
            datetime.datetime.strptime(time_input, "%H:%M")
        except ValueError:
            await update.message.reply_text(
                "❌ **invalid time format!** ⏰\n\n"
                "please use **HH:MM** format (24-hour):\n"
                "• **09:00** ✅\n"
                "• **14:30** ✅\n"
                "• **9:00** ❌ (use 09:00)\n"
                "• **2:30 PM** ❌ (use 14:30)\n\n"
                "try again! 😊"
            )
            return WAITING_DAILY_REMINDER_TIME
        
        # Save the daily reminder
        success = save_daily_reminder(user_id, reminder_text, time_input)
        
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if success:
            # Convert to 12-hour format for display
            time_obj = datetime.datetime.strptime(time_input, "%H:%M")
            display_time = time_obj.strftime("%I:%M %p").lstrip('0')
            
            await update.message.reply_text(
                f"✅ **daily reminder created successfully!** 📅\n\n"
                f"⏰ **time:** {display_time} ({time_input})\n"
                f"💬 **message:** \"{reminder_text}\"\n\n"
                f"📱 i'll send you this reminder every day at {display_time}! ✨\n\n"
                f"💡 you can manage your daily reminders from the main menu!",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ **failed to create daily reminder** 😅\n\n"
                "something went wrong while saving. please try again! 💕",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        return MENU
        
    except Exception as e:
        logger.error(f"Error processing daily reminder time: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "oops! something went wrong while setting up your daily reminder 😅",
            reply_markup=reply_markup
        )
        return MENU

async def handle_toggle_reminder(query, reminder_index: int) -> int:
    """
    Handle toggling a daily reminder on/off.
    
    Args:
        query: Telegram callback query object
        reminder_index: Index of the reminder to toggle
        
    Returns:
        int: MENU state
    """
    try:
        user_id = query.from_user.id
        success = toggle_daily_reminder(user_id, reminder_index)
        
        if success:
            await query.answer("✅ reminder status updated!")
            # Refresh the daily reminders menu
            return await handle_daily_reminders(query)
        else:
            await query.answer("❌ failed to update reminder status")
            return await show_main_menu_from_query(query)
            
    except Exception as e:
        logger.error(f"Error toggling reminder: {e}")
        await query.answer("❌ error occurred")
        return await show_main_menu_from_query(query)

async def handle_delete_reminder(query, reminder_index: int) -> int:
    """
    Handle deleting a daily reminder.
    
    Args:
        query: Telegram callback query object
        reminder_index: Index of the reminder to delete
        
    Returns:
        int: MENU state
    """
    try:
        user_id = query.from_user.id
        success = remove_daily_reminder(user_id, reminder_index)
        
        if success:
            await query.answer("🗑️ reminder deleted!")
            # Refresh the daily reminders menu
            return await handle_daily_reminders(query)
        else:
            await query.answer("❌ failed to delete reminder")
            return await show_main_menu_from_query(query)
            
    except Exception as e:
        logger.error(f"Error deleting reminder: {e}")
        await query.answer("❌ error occurred")
        return await show_main_menu_from_query(query)

# Partner reminder handlers
async def handle_partner_reminder(query) -> int:
    """
    Handle partner reminder button click and start reminder creation process.
    
    Args:
        query: Telegram callback query object
        
    Returns:
        int: WAITING_PARTNER_REMINDER_TEXT state to continue conversation
    """
    try:
        user_id = query.from_user.id
        user_role = get_user_role(user_id)
        partner_id = get_partner_user_id(user_id)
        
        if not user_role:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="⚠️ please set your role first! 💕",
                reply_markup=reply_markup
            )
            return MENU
        
        if not partner_id:
            keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="⚠️ couldn't find your partner! make sure they've set their role too! 💕\n\n"
                     "both of you need to use the bot and set your roles (boyfriend/girlfriend) to use partner reminders! ✨",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return MENU
        
        partner_role = "girlfriend" if user_role == "boyfriend" else "boyfriend"
        partner_name = get_user_name(partner_id) or f"your {partner_role}"
        
        await query.edit_message_text(
            text=f"💌 **set a reminder for {partner_name}!** 💌\n\n"
                 f"what would you like to remind {partner_name} about? just type your reminder message! 💕\n\n"
                 f"_(type /cancel to go back to menu)_",
            parse_mode='Markdown'
        )
        
        # Store partner info in context
        context_key = f"partner_reminder_{user_id}"
        # We'll use user_data in the actual handler
        
        return WAITING_PARTNER_REMINDER_TEXT
        
    except Exception as e:
        logger.error(f"Error in handle_partner_reminder: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="oops! partner reminder system had a hiccup 😅 try again later!",
            reply_markup=reply_markup
        )
        return MENU

async def process_partner_reminder_text(update: Update, context: CallbackContext) -> int:
    """
    Process the partner reminder text input from user.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: WAITING_PARTNER_REMINDER_TIME state to continue conversation
    """
    try:
        user_id = update.effective_user.id
        reminder_text = update.message.text.strip()
        partner_id = get_partner_user_id(user_id)
        
        if not partner_id:
            await update.message.reply_text("⚠️ **couldn't find your partner!** please try again later. 💕", parse_mode='Markdown')
            return MENU
        
        context.user_data['partner_reminder_text'] = reminder_text
        context.user_data['partner_id'] = partner_id
        
        partner_name = get_user_name(partner_id) or "your partner"
        
        await update.message.reply_text(
            f"📝 **reminder for {partner_name}:** \"{reminder_text}\" ✨\n\n"
            f"⏰ **when should i remind {partner_name}?** send me the time in format:\n"
            f"• **HH:MM** (e.g., 14:30 for 2:30 PM) 🕐\n"
            f"• or just say **now** for immediate reminder ⚡\n"
            f"• or **tomorrow** for same time tomorrow 📅\n\n"
            f"_(type /cancel to go back to menu)_ 💕",
            parse_mode='Markdown'
        )
        return WAITING_PARTNER_REMINDER_TIME
        
    except Exception as e:
        logger.error(f"Error processing partner reminder text: {e}")
        await update.message.reply_text("oops! something went wrong. let's start over with /start", parse_mode='Markdown')
        return MENU

async def process_partner_reminder_time(update: Update, context: CallbackContext) -> int:
    """
    Process the partner reminder time input and save the reminder.
    
    Args:
        update: Telegram update object
        context: Callback context
        
    Returns:
        int: MENU to return to main menu after setting partner reminder
    """
    try:
        time_input = update.message.text.lower().strip()
        reminder_text = context.user_data.get('partner_reminder_text', 'generic partner reminder')
        partner_id = context.user_data.get('partner_id')
        user_id = update.effective_user.id
        
        if not partner_id:
            await update.message.reply_text("⚠️ **error:** couldn't find partner information. please try again! 💕", parse_mode='Markdown')
            return MENU
        
        partner_name = get_user_name(partner_id) or "your partner"
        user_name = get_user_name(user_id) or "your partner"
        
        # Create back to menu keyboard
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if time_input == "now":
            # Send immediate partner reminder
            try:
                await update.message.bot.send_message(
                    chat_id=partner_id,
                    text=f"💌 **reminder from {user_name}!** 💌\n\n💕 hey! 💕\n\n📝 {user_name} wanted to remind you: {reminder_text}\n\n✨ they're thinking of you right now! ✨",
                    parse_mode='Markdown'
                )
                
                await update.message.reply_text(
                    f"✅ **immediate reminder sent to {partner_name}!** 💌\n\n"
                    f"📝 **message:** \"{reminder_text}\"\n\n"
                    f"they got your reminder right away! 💕", 
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            except Exception as send_error:
                logger.error(f"Error sending immediate partner reminder: {send_error}")
                await update.message.reply_text(
                    f"❌ **couldn't send immediate reminder to {partner_name}** 😅\n\n"
                    f"they might not have started the bot yet. try scheduling it for later instead! 💕",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
        elif time_input == "tomorrow":
            # Schedule for same time tomorrow
            now = datetime.datetime.now()
            tomorrow = now + datetime.timedelta(days=1)
            reminder_datetime = tomorrow.replace(second=0, microsecond=0)
            
            success = save_partner_reminder(user_id, partner_id, reminder_text, reminder_datetime.isoformat())
            
            if success:
                await update.message.reply_text(
                    f"✅ **partner reminder scheduled for tomorrow!** 📅\n\n"
                    f"👤 **for:** {partner_name}\n"
                    f"⏰ **time:** {reminder_datetime.strftime('%B %d, %Y at %I:%M %p')}\n"
                    f"📝 **message:** \"{reminder_text}\"\n\n"
                    f"i'll remind {partner_name} tomorrow! 💕",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ failed to schedule partner reminder. please try again! 😅",
                    reply_markup=reply_markup
                )
                
        elif ":" in time_input:
            # Parse time format HH:MM
            try:
                time_obj = datetime.datetime.strptime(time_input, "%H:%M")
                now = datetime.datetime.now()
                
                # Schedule for today if time hasn't passed, otherwise tomorrow
                reminder_datetime = now.replace(
                    hour=time_obj.hour, 
                    minute=time_obj.minute, 
                    second=0, 
                    microsecond=0
                )
                
                if reminder_datetime <= now:
                    # Time has passed today, schedule for tomorrow
                    reminder_datetime += datetime.timedelta(days=1)
                
                success = save_partner_reminder(user_id, partner_id, reminder_text, reminder_datetime.isoformat())
                
                if success:
                    display_time = reminder_datetime.strftime("%I:%M %p").lstrip('0')
                    day_text = "today" if reminder_datetime.date() == now.date() else "tomorrow"
                    
                    await update.message.reply_text(
                        f"✅ **partner reminder scheduled!** 💌\n\n"
                        f"👤 **for:** {partner_name}\n"
                        f"⏰ **time:** {day_text} at {display_time}\n"
                        f"📝 **message:** \"{reminder_text}\"\n\n"
                        f"i'll remind {partner_name} {day_text}! 💕",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "❌ failed to schedule partner reminder. please try again! 😅",
                        reply_markup=reply_markup
                    )
                    
            except ValueError:
                await update.message.reply_text(
                    f"❌ **invalid time format!** ⏰\n\n"
                    f"please use **HH:MM** format (24-hour):\n"
                    f"• **09:00** ✅\n"
                    f"• **14:30** ✅\n"
                    f"• **9:00** ❌ (use 09:00)\n"
                    f"• **2:30 PM** ❌ (use 14:30)\n\n"
                    f"or use:\n"
                    f"• **now** for immediate reminder ⚡\n"
                    f"• **tomorrow** for same time tomorrow 📅\n\n"
                    f"try again! 😊",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return WAITING_PARTNER_REMINDER_TIME
        else:
            await update.message.reply_text(
                f"❌ **couldn't understand time format!** 😅\n\n"
                f"please try:\n"
                f"• **HH:MM** format (e.g., 14:30) ⏰\n"
                f"• **now** for immediate reminder ⚡\n"
                f"• **tomorrow** for same time tomorrow 📅\n\n"
                f"your reminder for {partner_name}: \"{reminder_text}\" is waiting! 💕",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return WAITING_PARTNER_REMINDER_TIME
        
        return MENU
    
    except Exception as e:
        logger.error(f"Error processing partner reminder time: {e}")
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "oops! partner reminder system had a hiccup 😅 but your love got through anyway! 💕",
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
            await update.message.reply_text("⚠️ **error:** role not found. please set your role first! 💕", parse_mode='Markdown')
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
            await update.message.reply_text("⚠️ **error:** role not found. please set your role first! 💕", parse_mode='Markdown')
            return MENU
        
        # Get the video
        video = update.message.video
        if not video:
            # Try video note (circular videos)
            video = update.message.video_note
        
        if not video:
            await update.message.reply_text("⚠️ **please send a video file!** 📹", parse_mode='Markdown')
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
        await update.message.reply_text(f"**{text}?** okay buddy... /start to chat bro... 😎", parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error processing text input: {e}")
        await update.message.reply_text("sorry something broke... 😅", parse_mode='Markdown')
    
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
        [InlineKeyboardButton("📅 daily reminders", callback_data="daily_reminders")]
    ]
    
    # Add role-specific submission options and partner reminders
    if user_role:
        keyboard.extend([
            [InlineKeyboardButton("📤 submit photo for partner", callback_data="submit_photo")],
            [InlineKeyboardButton("🫧 submit bubble for partner", callback_data="submit_bubble")],
            [InlineKeyboardButton("💌 set reminder for partner", callback_data="partner_reminder")]
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
    
    # Get current times for both locations
    times = get_current_times()
    time_info = f"\n\n🕐 **current times** 🕐\n🇨🇿 **prague:** {times['prague']['full']}\n🇺🇸 **new orleans:** {times['new_orleans']['full']}"
    
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
            "• daily reminders 📅\n"
            "• partner reminders 💌\n\n"
            "**plus, you can now submit content for your partner!** ✨\n\n"
            "**choose what you need right now! ✨**\n"
            "_(i'll keep running until you type /stop or click exit)_ 💕"
            f"{time_info}"
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
            "• reminders ⏰\n\n"
            "_(i'll keep running until you type /stop or click exit)_ ✨"
            f"{time_info}"
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
    elif query.data == "daily_reminders":
        return await handle_daily_reminders(query)
    elif query.data == "add_daily_reminder":
        return await handle_add_daily_reminder(query)
    elif query.data.startswith("toggle_reminder_"):
        reminder_index = int(query.data.split("_")[-1])
        return await handle_toggle_reminder(query, reminder_index)
    elif query.data.startswith("delete_reminder_"):
        reminder_index = int(query.data.split("_")[-1])
        return await handle_delete_reminder(query, reminder_index)
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
    elif query.data == "partner_reminder":
        return await handle_partner_reminder(query)
    elif query.data == "back_to_menu":
        return await show_main_menu_from_query(query)
    elif query.data == "exit":
        await query.edit_message_text(
            text="**goodbye love!** thanks for letting me brighten your day 💕✨\n\ntype /start anytime to chat again!",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    else:
        keyboard = [[InlineKeyboardButton("🔙 back to menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="**unknown option selected.** let's try again! 🔄",
            reply_markup=reply_markup,
            parse_mode='Markdown'
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
    await update.message.reply_text("**goodbye love!** thanks for letting me brighten your day 💕✨\n\ntype /start anytime to chat again!", parse_mode='Markdown')
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
        [InlineKeyboardButton("⏰ set a reminder", callback_data="reminder")]
    ]
    
    # Add role-specific submission options and partner reminders
    if user_role:
        keyboard.extend([
            [InlineKeyboardButton("📤 submit photo for partner", callback_data="submit_photo")],
            [InlineKeyboardButton("🫧 submit bubble for partner", callback_data="submit_bubble")],
            [InlineKeyboardButton("💌 set reminder for partner", callback_data="partner_reminder")]
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
    
    # Get current times for both locations
    times = get_current_times()
    time_info = f"\n\n🕐 **current times** 🕐\n🇨🇿 **prague:** {times['prague']['full']}\n🇺🇸 **new orleans:** {times['new_orleans']['full']}"
    
    if user_role:
        message_text = f"💫 **back to the main menu!** 💫\nrole: **{user_role}** 👤\n\nwhat would you like to do next? ✨{time_info}"
    else:
        message_text = f"💫 **back to the main menu!** 💫\n⚠️ please set your role first to access all features! 💕\n\nwhat would you like to do? ✨{time_info}"
    
    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return MENU

# Version command handler
async def version(update: Update, context: CallbackContext) -> None:
    """
    Handle /version command and display bot version and author information.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    VERSION_NUMBER = "1.0.1"
    try:
        version_info = (
            "🤖 **anselmbot version info** 🤖\n\n"
            f"📍 **version:** {VERSION_NUMBER}\n"
            "👨‍💻 **author:** Anselm Long\n"
            "💕 **purpose:** making long-distance love a little easier i hope ✨\n\n"
        )
        
        await update.message.reply_text(
            version_info,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in version command: {e}")
        await update.message.reply_text(
            "🤖 **anselmbot** v1.0.0 by Anselm Long 💕\n"
            "oops! something went wrong displaying version info 😅",
            parse_mode='Markdown'
        )

# Reminders command handler
async def reminders(update: Update, context: CallbackContext) -> None:
    """
    Handle /reminders command to show all active reminders for the user.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        user_id = update.effective_user.id
        user_name = get_user_name(user_id)
        
        # Get all types of reminders
        daily_reminders = get_user_daily_reminders(user_id)
        one_time_reminders = get_user_one_time_reminders(user_id)
        partner_reminders = get_user_partner_reminders(user_id)
        
        # Filter out sent reminders
        pending_one_time = [r for r in one_time_reminders if not r.get('sent', False)]
        pending_partner = [r for r in partner_reminders if not r.get('sent', False)]
        
        if not daily_reminders and not pending_one_time and not pending_partner:
            await update.message.reply_text(
                f"📋 **your reminders** 📋\n\n"
                f"you have no active reminders right now! 😊\n\n"
                f"use /start to set up some reminders! ✨",
                parse_mode='Markdown'
            )
            return
        
        message = f"📋 **your active reminders** 📋\n\n"
        
        if daily_reminders:
            message += "🔄 **daily reminders:**\n"
            for i, reminder in enumerate(daily_reminders):
                status = "✅" if reminder.get('active', True) else "❌"
                time_obj = datetime.datetime.strptime(reminder['time'], "%H:%M")
                display_time = time_obj.strftime("%I:%M %p").lstrip('0')
                message += f"{i+1}. {status} **{display_time}** - {reminder['text']}\n"
            message += "\n"
        
        if pending_one_time:
            message += "⏰ **scheduled reminders:**\n"
            for i, reminder in enumerate(pending_one_time):
                try:
                    reminder_dt = datetime.datetime.fromisoformat(reminder['datetime'])
                    display_dt = reminder_dt.strftime("%B %d, %Y at %I:%M %p")
                    message += f"{i+1}. **{display_dt}** - {reminder['text']}\n"
                except ValueError:
                    message += f"{i+1}. **invalid date** - {reminder['text']}\n"
            message += "\n"
        
        if pending_partner:
            message += "💌 **partner reminders for you:**\n"
            for i, reminder in enumerate(pending_partner):
                try:
                    reminder_dt = datetime.datetime.fromisoformat(reminder['datetime'])
                    display_dt = reminder_dt.strftime("%B %d, %Y at %I:%M %p")
                    sender_name = reminder.get('sender_name', 'your partner')
                    message += f"{i+1}. **{display_dt}** from {sender_name}: {reminder['text']}\n"
                except ValueError:
                    sender_name = reminder.get('sender_name', 'your partner')
                    message += f"{i+1}. **invalid date** from {sender_name}: {reminder['text']}\n"
            message += "\n"
        
        message += "💡 use /start to manage your reminders! ✨"
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in reminders command: {e}")
        await update.message.reply_text(
            "**oops!** something went wrong checking your reminders 😅\n"
            "use /start to access the reminder system! 💕",
            parse_mode='Markdown'
        )

# Timezone command handler
async def timezone(update: Update, context: CallbackContext) -> None:
    """
    Handle /timezone command to show current times in both locations.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    try:
        times = get_current_times()
        
        message = (
            "🌍 **worldwide couple times** 🌍\n\n"
            f"🇨🇿 **prague, czech republic**\n"
            f"⏰ {times['prague']['full']}\n\n"
            f"🇺🇸 **new orleans, usa**\n" 
            f"⏰ {times['new_orleans']['full']}\n\n"
            "💕 love knows no distance or time zone! ✨"
        )
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in timezone command: {e}")
        await update.message.reply_text(
            "**oops!** something went wrong checking the time 😅\n"
            "maybe time is relative after all! 💕",
            parse_mode='Markdown'
        )

# Main function to start the bot
def main():
    """
    Main function to initialize and start the Telegram bot.
    Sets up conversation handlers and starts polling for updates.
    """
    global reminder_scheduler
    
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .read_timeout(10)
        .write_timeout(10)
        .concurrent_updates(True)
        .build()
    )

    # Initialize and start the daily reminder scheduler
    reminder_scheduler = DailyReminderScheduler(application)
    reminder_scheduler.start()

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
            WAITING_DAILY_REMINDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_daily_reminder_text)],
            WAITING_DAILY_REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_daily_reminder_time)],
            WAITING_PARTNER_REMINDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_partner_reminder_text)],
            WAITING_PARTNER_REMINDER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_partner_reminder_time)],
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
    
    # Add version command handler
    application.add_handler(CommandHandler("version", version))
    
    # Add reminders command handler
    application.add_handler(CommandHandler("reminders", reminders))
    
    # Add timezone command handler
    application.add_handler(CommandHandler("timezone", timezone))
    
    logger.info("Bot started successfully! 🤖💕")
    logger.info("Bot will keep running and return to menu after each action")
    logger.info("Users can type /stop, /exit, /cancel, or click 'exit bot' to quit")
    logger.info("Role-based system enabled - users can be 'boyfriend' or 'girlfriend'")
    logger.info("Content submission enabled - partners can submit photos and bubbles for each other")
    logger.info("Daily reminder scheduler is running! 📅")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        # Clean up the scheduler
        if reminder_scheduler:
            reminder_scheduler.stop()
        logger.info("Daily reminder scheduler stopped! 📅")

if __name__ == "__main__":
    main()