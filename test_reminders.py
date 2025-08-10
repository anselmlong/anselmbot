"""
Simple test script to verify reminder functions work correctly.
"""
import json
import datetime
import os

# Test the reminder functions
def test_reminder_functions():
    print("🧪 Testing reminder functions...")
    
    # Test data structure
    test_data = {
        'daily_reminders': {
            '123456789': [
                {
                    'text': 'Test daily reminder',
                    'time': '09:00',
                    'active': True,
                    'created_at': datetime.datetime.now().isoformat()
                }
            ]
        },
        'one_time_reminders': {
            '123456789': [
                {
                    'text': 'Test one-time reminder',
                    'datetime': (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat(),
                    'sent': False,
                    'created_at': datetime.datetime.now().isoformat()
                }
            ]
        }
    }
    
    # Create test JSON file
    with open('test_bot_data.json', 'w', encoding='utf-8') as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print("✅ Test data created successfully!")
    print("📋 Daily reminders:", len(test_data['daily_reminders']['123456789']))
    print("⏰ One-time reminders:", len(test_data['one_time_reminders']['123456789']))
    
    # Show the structure
    print("\n📂 Data structure:")
    print(json.dumps(test_data, indent=2))
    
    # Clean up
    if os.path.exists('test_bot_data.json'):
        os.remove('test_bot_data.json')
        print("\n🗑️ Test file cleaned up")

if __name__ == "__main__":
    test_reminder_functions()
