# Function Documentation 📚

## Overview
This document provides detailed technical documentation for all functions in the LDR Telegram Bot.

## Handler Functions

### `handle_joke(query) -> int`
**File**: `buttons.py` (Line ~90)  
**Purpose**: Handles the "tell me a joke" button functionality  
**User Story**: "As a girlfriend, I want to see jokes from my boyfriend so that I can cheer up"

**Process Flow**:
1. Loads `bot_data.json` using `load_json_data()`
2. Validates that `jokes` array exists and is not empty
3. Randomly selects a joke using `random.choice()`
4. Sends joke with 😂 emoji formatting
5. Returns `ConversationHandler.END` to terminate conversation

**Error Handling**:
- Missing/empty jokes array: Sends fallback funny message
- JSON loading errors: Logged and fallback message sent
- General exceptions: Caught and logged with appropriate user message

**Data Dependencies**: `bot_data.json → jokes[]`

---

### `handle_flirt(query) -> None`
**File**: `buttons.py` (Line ~60)  
**Purpose**: Sends flirty pickup lines and romantic messages  
**User Story**: Core feature for maintaining romantic connection in LDR

**Process Flow**:
1. Loads flirt messages from `bot_data.json`
2. Validates flirt_messages array availability
3. Randomly selects message
4. Formats with 💕 emoji and sends
5. Conversation ends automatically (returns None)

**Error Handling**:
- Empty data: "tongue-tied" fallback message
- Exceptions: "rizz game" error message

---

### `handle_picture(query) -> int`
**File**: `buttons.py` (Line ~115)  
**Purpose**: Sends random images of partner to user  
**User Story**: "As a girlfriend, I want to see a random picture of my boyfriend so that I can laugh"

**Process Flow**:
1. Loads image paths from `bot_data.json`
2. Converts relative paths to absolute paths
3. Checks file existence for each image
4. Filters to available images only
5. Randomly selects available image
6. Deletes original menu message
7. Sends photo with caption

**File Handling**:
- Supports: .jpg, .jpeg, .png, .gif, .webp
- Local file system only (no cloud storage)
- Automatic path resolution from script directory
- File existence validation before sending

**Error Scenarios**:
- No image paths configured: Camera shy message
- No images found on disk: Check back later message
- File access errors: Camera broken message

**Security Considerations**:
- Only sends pre-configured images
- No directory traversal vulnerabilities
- User controls all image content

---

### `handle_bubble(query) -> int`
**File**: `buttons.py` (Line ~165)  
**Purpose**: Sends cute short messages in bubble format  
**User Story**: Provides quick emotional connection and affection

**Message Format**: `🫧 {message} 🫧`

**Process Flow**:
1. Loads telebubbles from JSON data
2. Randomly selects message
3. Wraps with bubble emojis
4. Sends formatted message

**Content Types**:
- Missing/longing messages
- Love declarations  
- Cute everyday thoughts
- Meeting countdown expressions

---

### `handle_motivation(query) -> int`
**File**: `buttons.py` (Line ~185)  
**Purpose**: Provides encouraging pep talks and motivational quotes  
**User Story**: Support during difficult times in LDR

**Message Categories**:
- Strength reminders
- Past achievement references
- Future-focused encouragement
- Metaphorical comparisons (diamonds, phoenixes)
- Personal affirmations

**Psychological Approach**:
- Acknowledges current difficulties
- References past successes
- Uses empowering language
- Maintains personal connection

---

### `handle_location(query) -> int`
**File**: `buttons.py` (Line ~205)  
**Purpose**: Provides general location/status updates safely  
**User Story**: "As a partner, I want to see my partner's location so that I can be assured he is safe"

**Privacy-First Design**:
- **No GPS coordinates** shared
- **No exact addresses** revealed
- General status messages only
- Customizable responses

**Message Types**:
- General safety confirmations
- Activity-based locations (library, home, etc.)
- Emotional status with location context
- Romantic location references

**Security Benefits**:
- Maintains safety assurance
- Prevents location tracking
- User-controlled information sharing

---

### `handle_stats(query) -> int`
**File**: `buttons.py` (Line ~235)  
**Purpose**: Displays comprehensive relationship and exchange program statistics  
**User Story**: "As a user, I want to see statistics about our exchange programme so that I can know how long more we have left"

**Calculated Statistics**:
1. **Exchange Days Left**: Uses `days_from_today()` with end_date
2. **Relationship Duration**: Uses `calculate_days_between()` with start date and today
3. **Days Until Meeting**: Uses `days_from_today()` with next_meeting date

**Display Features**:
- Markdown formatting for emphasis
- Special handling for TODAY scenarios
- Past/present/future date logic
- Years + days breakdown for long relationships
- Emoji-rich presentation

**Date Handling Edge Cases**:
- Past dates: Shows "X days ago"
- Today: Shows "TODAY!" with celebration emojis
- Future dates: Shows countdown
- Invalid dates: Graceful fallback

**Data Dependencies**: `bot_data.json → exchange_stats{}`

---

### `handle_reminder(query) -> int`
**File**: `buttons.py` (Line ~280)  
**Purpose**: Initiates multi-step reminder creation process  
**User Story**: "Create reminders for each other + alert function"

**Conversation Flow**:
1. `handle_reminder()`: Prompts for reminder text
2. `process_reminder_text()`: Captures text, prompts for time
3. `process_reminder_time()`: Processes time, completes setup

**States Used**:
- `WAITING_REMINDER_TEXT`: Waiting for reminder content
- `WAITING_REMINDER_TIME`: Waiting for time specification

**Time Input Formats**:
- `"now"`: Immediate reminder
- `"tomorrow"`: Same time next day
- `"HH:MM"`: Specific time format
- Free text: General reminder note

**Current Limitations**:
- Demo implementation only
- No persistent scheduling
- No actual time-based triggers
- Future enhancement needed: APScheduler integration

---

### `handle_restaurant(query) -> int`
**File**: `buttons.py` (Line ~340)  
**Purpose**: Suggests restaurants based on curated reviews  
**User Story**: "Where to eat: Find place to eat based on reviews"

**Display Format**:
```
🍽️ **Restaurant Name** 🍽️

📍 Type: Category
📝 Description
⭐ Rating: X.X/5  
✨ Vibe: atmosphere description

bon appétit, babe! 😘🍴
```

**Data Structure**:
```json
{
  "name": "Restaurant Name",
  "type": "Category",
  "description": "What makes it special", 
  "rating": "4.5/5",
  "vibe": "Atmosphere description"
}
```

**Customization Options**:
- Add local favorites
- Include dietary restrictions
- Add price ranges
- Include distance/location info

---

## Utility Functions

### `load_json_data(filename: str) -> dict`
**Purpose**: Safely loads JSON configuration files  
**Error Handling**: Returns empty dict on failure, comprehensive logging

**Process**:
1. Resolves absolute path from script directory
2. Opens with UTF-8 encoding
3. Parses JSON content
4. Returns data or empty dict

**Exception Handling**:
- `FileNotFoundError`: Logged, empty dict returned
- `json.JSONDecodeError`: Logged, empty dict returned  
- General exceptions: Logged, empty dict returned

### `save_json_data(filename: str, data: dict) -> bool`
**Purpose**: Saves data to JSON files with proper formatting  
**Returns**: Success/failure boolean

**Features**:
- Pretty printing with indent=2
- UTF-8 encoding preservation
- Comprehensive error logging

### `calculate_days_between(start_date: str, end_date: str) -> int`
**Purpose**: Calculates days between two dates  
**Format**: Expects YYYY-MM-DD format strings

**Process**:
1. Parses date strings using `strptime()`
2. Calculates timedelta
3. Returns days as integer
4. Returns 0 on error

### `days_from_today(target_date: str) -> int`
**Purpose**: Calculates days from today to target date  
**Returns**: Negative for past dates, positive for future dates

**Usage Examples**:
- Future meeting: +45 (45 days from now)
- Past event: -30 (30 days ago)
- Today: 0

## Conversation Handler Architecture

### States
- `MENU`: Main menu button handling
- `WAITING_REMINDER_TEXT`: Collecting reminder message
- `WAITING_REMINDER_TIME`: Collecting reminder time

### Entry Points
- `/start` command: Shows main menu
- Direct button interactions

### Fallbacks
- `/cancel` command: Graceful conversation exit
- `/start` command: Return to main menu

### State Transitions
```
START → MENU → (button selection) → END
            → REMINDER → WAITING_TEXT → WAITING_TIME → END
```

## Error Handling Philosophy

### Graceful Degradation
- Always provide user feedback
- Never leave user hanging
- Fallback to basic functionality
- Maintain conversational tone

### Logging Strategy
- All errors logged with context
- User-friendly error messages
- Technical details in logs only
- Consistent error message tone

### User Experience
- Errors don't break conversation flow
- Helpful suggestions when possible
- Consistent emoji usage
- Maintains bot personality even in errors

## Security Considerations

### Data Privacy
- Local file storage only
- No cloud service dependencies
- User controls all personal content
- No sensitive data logging

### Input Validation
- File existence checks
- Path traversal prevention
- JSON validation
- Date format validation

### Bot Token Security
- Environment variable storage
- No hardcoded credentials
- .env file excluded from version control

## Performance Considerations

### File I/O Optimization
- JSON loaded once per request
- Image existence cached during selection
- Minimal file system operations

### Memory Usage
- No persistent data caching
- JSON data loaded as needed
- Images served directly (no memory buffering)

### Response Time
- Local file operations only
- No external API dependencies
- Immediate response for most features

## Extension Points

### Easy Additions
- New message categories in JSON
- Additional restaurant data
- Custom location messages
- More statistical calculations

### Architecture Extensions
- Database backend for persistence
- Scheduled task integration
- External API integration
- Multi-user support

### Feature Extensions
- Voice message handling
- Video message support
- File sharing capabilities
- Advanced reminder scheduling
