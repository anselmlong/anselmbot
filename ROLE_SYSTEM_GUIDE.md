# Role-Based System Guide

## Overview
The bot now supports a **role-based system** where users can be either a **boyfriend** or **girlfriend**. Each role has access to different content and can submit content for their partner.

## How It Works

### 1. Role Assignment
- When users first start the bot, they need to set their role
- Click "👤 set my role" to choose between boyfriend or girlfriend
- Once set, users can change their role anytime by clicking their role button

### 2. Role-Based Content
- **Pictures**: Each role sees different photos submitted by their partner
- **Telebubbles**: Each role receives different bubble messages from their partner
- **Other content** (jokes, flirt messages, motivation, etc.) remains shared

### 3. Content Submission
Users can submit content for their partner:
- **📤 submit photo for partner**: Upload photos that your partner will see
- **🫧 submit bubble for partner**: Write bubble messages for your partner

## File Structure

### bot_data.json
```json
{
  "content": {
    "boyfriend": {
      "image_paths": ["images/boyfriend/photo1.jpg"],
      "telebubbles": ["message from girlfriend"]
    },
    "girlfriend": {
      "image_paths": ["images/girlfriend/photo1.jpg"], 
      "telebubbles": ["message from boyfriend"]
    }
  },
  "user_roles": {
    "123456789": "boyfriend",
    "987654321": "girlfriend"
  }
}
```

### Directory Structure
```
anselmbot/
├── images/
│   ├── boyfriend/          # Photos that boyfriend will see (submitted by girlfriend)
│   ├── girlfriend/         # Photos that girlfriend will see (submitted by boyfriend)
│   └── [legacy files]      # Original shared photos (fallback)
├── main.py
├── bot_data.json
└── ROLE_SYSTEM_GUIDE.md
```

## Features

### For Users
1. **Role Selection**: Choose boyfriend or girlfriend role
2. **Role-Specific Content**: See content tailored to your role
3. **Content Submission**: Submit photos and bubbles for your partner
4. **Fallback Support**: If no role-specific content exists, falls back to shared content

### For Developers
1. **Backward Compatibility**: Existing content still works for users without roles
2. **Extensible**: Easy to add more role-specific content types
3. **Error Handling**: Graceful fallbacks when content is missing
4. **File Management**: Automatic directory creation and file organization

## Technical Implementation

### Key Functions
- `get_user_role(user_id)`: Get user's current role
- `set_user_role(user_id, role)`: Set user's role
- `get_role_based_content(content_type, user_role)`: Get content for specific role
- `save_content_for_partner(content_type, content_data, submitter_role)`: Save content for partner

### Conversation States
- `WAITING_PHOTO_UPLOAD`: Waiting for photo submission
- `WAITING_BUBBLE_TEXT`: Waiting for bubble text submission

### Message Handlers
- `process_photo_upload()`: Handle photo submissions
- `process_bubble_text()`: Handle bubble text submissions

## Usage Examples

### Setting Role
1. Start bot with `/start`
2. Click "👤 set my role"
3. Choose "💙 I'm the boyfriend" or "💖 I'm the girlfriend"

### Submitting Content
1. Click "📤 submit photo for partner"
2. Send a photo
3. Photo is saved to partner's collection

### Viewing Content
1. Click "📸 i wanna see you"
2. Receives random photo from partner's submissions
3. If no partner content exists, falls back to shared content

## Benefits

1. **Personalized Experience**: Each partner gets content specifically from the other
2. **Interactive**: Partners can actively contribute to each other's experience  
3. **Organized**: Content is properly separated and organized by role
4. **Scalable**: Easy to extend with more role-specific features
5. **Safe**: No mixing of personal content between different relationships

## Future Enhancements

Potential additions:
- Role-specific flirt messages
- Role-specific motivation messages
- Content approval system
- Content expiration dates
- Content statistics/analytics
- Multiple partner support
- Content categories/tags
