# LDR Telegram Bot 💕🤖

A Python Telegram bot designed specifically for long-distance relationships (LDR). This bot helps couples stay connected by providing jokes, flirty messages, pictures, motivation, location updates, relationship statistics, reminders, and restaurant suggestions.

## Features ✨

### Core Features
- **😂 Jokes**: Sends random jokes to cheer up your partner
- **💕 Flirt Messages**: Delivers sweet pickup lines and flirty messages
- **📸 Random Pictures**: Sends random images of your partner (when configured)
- **🫧 Telebubbles**: Cute short messages in bubble format
- **💪 Motivation**: Provides encouraging pep talks and motivational quotes
- **📍 Location Updates**: Shows general location/status updates (privacy-safe)
- **📊 Relationship Stats**: Displays exchange program progress, relationship duration, and meeting countdowns
- **⏰ Reminders**: Create and manage reminders for each other
- **🍽️ Restaurant Suggestions**: Recommends places to eat based on curated reviews

## User Stories Fulfilled 📝

### For Girlfriends
- ✅ **See jokes from boyfriend**: Random joke delivery to brighten the day
- ✅ **See random pictures**: Image sharing functionality (requires setup)
- ✅ **Hear voice/video notes**: Framework in place (can be extended)

### For Users
- ✅ **Exchange program statistics**: Countdown timers and progress tracking
- ✅ **Location awareness**: Safe location sharing without exact coordinates

### For Partners  
- ✅ **Input various media types**: Support for text, images, and expandable to voice/video
- ✅ **Make partner happy**: Multiple features designed to spread joy

## Installation & Setup 🔧

### Prerequisites
- Python 3.7+
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))

### Step 1: Clone and Install Dependencies
```bash
git clone <repository-url>
cd anselmbot
pip install -r requirements.txt
```

### Step 2: Environment Setup
Create a `.env` file in the project root:
```env
BOT_TOKEN=your_bot_token_here
```

### Step 3: Configure Bot Data
Edit `bot_data.json` to customize:

#### Exchange Statistics
```json
"exchange_stats": {
  "start_date": "2024-08-15",      # Exchange program start
  "end_date": "2025-12-20",        # Exchange program end  
  "relationship_start": "2023-06-10", # When you started dating
  "next_meeting": "2025-08-01"     # Next planned meeting
}
```

#### Image Setup
1. Add images to the `images/` directory
2. Update the `image_paths` array in `bot_data.json`:
```json
"image_paths": [
  "images/pic1.jpg",
  "images/pic2.jpg",
  "images/cute_selfie.png"
]
```

### Step 4: Run the Bot
```bash
python buttons.py
```

## Function Documentation 📚

### Core Handler Functions

#### `handle_joke(query) -> int`
**Purpose**: Sends random jokes to cheer up the user  
**Data Source**: `bot_data.json` → `jokes` array  
**Returns**: `ConversationHandler.END`  
**User Story**: "As a girlfriend, I want to see jokes from my boyfriend so that I can cheer up"

#### `handle_flirt(query) -> None`  
**Purpose**: Delivers flirty pickup lines and romantic messages  
**Data Source**: `bot_data.json` → `flirt_messages` array  
**Returns**: None (ends conversation)  
**Features**: Randomized selection, emoji formatting

#### `handle_picture(query) -> int`
**Purpose**: Sends random images of partner  
**Data Source**: `bot_data.json` → `image_paths` array  
**Process**:
1. Loads available image paths
2. Checks file existence
3. Selects random image
4. Sends via Telegram photo API
**User Story**: "As a girlfriend, I want to see a random picture of my boyfriend so that I can laugh"

#### `handle_bubble(query) -> int`
**Purpose**: Sends cute short messages in bubble format  
**Data Source**: `bot_data.json` → `telebubbles` array  
**Format**: Wrapped with bubble emojis (🫧)

#### `handle_motivation(query) -> int`
**Purpose**: Provides encouraging pep talks and motivational content  
**Data Source**: `bot_data.json` → `pep_talks` array  
**Features**: Personalized messages, empowering language  
**User Story**: Support during difficult times in LDR

#### `handle_location(query) -> int`
**Purpose**: Shares general location/status updates safely  
**Security**: No exact coordinates, only general status messages  
**User Story**: "As a partner, I want to see my partner's location so that I can be assured he is safe"

#### `handle_stats(query) -> int`  
**Purpose**: Displays comprehensive relationship and exchange statistics  
**Calculations**:
- Days remaining in exchange program
- Total relationship duration (years + days)
- Days until next meeting
- Special handling for past/present dates
**User Story**: "As a user, I want to see statistics about our exchange programme so that I can know how long more we have left"

#### `handle_reminder(query) -> int`
**Purpose**: Initiates reminder creation process  
**Process**: Multi-state conversation for text and time input  
**States**: `WAITING_REMINDER_TEXT` → `WAITING_REMINDER_TIME`  
**Note**: Demo implementation (real scheduling requires task scheduler integration)

#### `handle_restaurant(query) -> int`
**Purpose**: Suggests restaurants based on curated reviews  
**Data Source**: `bot_data.json` → `restaurant_suggestions` array  
**Display**: Name, type, description, rating, vibe

### Utility Functions

#### `load_json_data(filename: str) -> dict`
**Purpose**: Safely loads JSON configuration files  
**Error Handling**: Returns empty dict on failure, logs errors  
**Usage**: All data-dependent handlers use this function

#### `save_json_data(filename: str, data: dict) -> bool`  
**Purpose**: Saves data back to JSON files  
**Returns**: Success/failure boolean  
**Usage**: Future extension for user preferences

#### `calculate_days_between(start_date: str, end_date: str) -> int`
**Purpose**: Calculates days between two dates  
**Format**: Expects YYYY-MM-DD format  
**Usage**: Relationship duration calculations

#### `days_from_today(target_date: str) -> int`
**Purpose**: Calculates days from today to target date  
**Returns**: Negative for past dates, positive for future  
**Usage**: Countdown timers, meeting schedules

## Data Structure 📊

### bot_data.json Schema
```json
{
  "flirt_messages": ["array of flirty messages"],
  "jokes": ["array of jokes"],  
  "pep_talks": ["array of motivational messages"],
  "telebubbles": ["array of short cute messages"],
  "restaurant_suggestions": [
    {
      "name": "Restaurant Name",
      "type": "Category", 
      "description": "Description",
      "rating": "X.X/5",
      "vibe": "atmosphere description"
    }
  ],
  "exchange_stats": {
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD", 
    "relationship_start": "YYYY-MM-DD",
    "next_meeting": "YYYY-MM-DD"
  },
  "image_paths": ["relative/path/to/images"]
}
```

## Customization Guide 🎨

### Adding New Jokes
```json
"jokes": [
  "your new joke here! 😂",
  "another hilarious joke 🤣"
]
```

### Adding New Restaurants
```json
"restaurant_suggestions": [
  {
    "name": "Your Favorite Spot",
    "type": "Cuisine Type",
    "description": "what makes it special",
    "rating": "4.5/5", 
    "vibe": "romantic, cozy, perfect for dates"
  }
]
```

### Updating Statistics
Simply modify the dates in the `exchange_stats` object. The bot automatically calculates:
- Days remaining/elapsed
- Relationship milestones  
- Meeting countdowns

## Security & Privacy 🔒

### Location Sharing
- **No exact coordinates** are shared
- Only general status messages
- Customizable location responses
- Privacy-first approach

### Image Handling
- Local file storage only
- No cloud uploads
- User controls all image content
- Automatic file existence checking

## Extension Ideas 🚀

### Immediate Improvements
1. **Real Reminder System**: Integrate with task scheduler (APScheduler)
2. **Voice Message Support**: Add audio file handling
3. **Video Message Support**: Add video file handling  
4. **Weather Integration**: Location-based weather updates
5. **Anniversary Tracking**: Automatic milestone celebrations

### Advanced Features (Future Scope)
1. **LLM Integration**: Train on chat history for natural responses
2. **Sentiment Analysis**: Mood-based response adaptation
3. **Calendar Integration**: Shared calendar management
4. **Photo Storage**: Cloud-based image management
5. **Multi-language Support**: Localization features

## Troubleshooting 🔧

### Common Issues

**Bot doesn't respond**: Check BOT_TOKEN in .env file  
**Images not sending**: Verify image paths and file permissions  
**Stats showing wrong dates**: Update exchange_stats in bot_data.json  
**Reminders not working**: This is demo functionality - implement proper scheduling

### Logging
All errors are logged with timestamps. Check console output for debugging information.

## Contributing 🤝

Feel free to:
- Add more jokes, flirt messages, or pep talks
- Improve error handling
- Add new features
- Submit bug reports
- Suggest enhancements

---

Made with ❤️ for long-distance couples everywhere. Distance means nothing when love means everything! 💕✨
