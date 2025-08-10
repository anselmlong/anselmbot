"""
Test partner reminder functionality
"""
import json
import datetime

def test_partner_reminders():
    print("🧪 Testing partner reminder data structure...")
    
    # Test data with partner reminders
    test_data = {
        'user_roles': {
            '123456789': 'boyfriend',
            '987654321': 'girlfriend'
        },
        'user_names': {
            '123456789': 'Anselm',
            '987654321': 'Partner'
        },
        'partner_reminders': {
            '987654321': [  # girlfriend receives reminder from boyfriend
                {
                    'text': 'dont forget to drink water babe!',
                    'datetime': (datetime.datetime.now() + datetime.timedelta(hours=2)).isoformat(),
                    'sent': False,
                    'sender_id': 123456789,
                    'sender_name': 'Anselm',
                    'created_at': datetime.datetime.now().isoformat()
                }
            ]
        }
    }
    
    print("✅ Partner reminder structure created!")
    print("📋 Sample partner reminder:")
    partner_reminder = test_data['partner_reminders']['987654321'][0]
    
    reminder_dt = datetime.datetime.fromisoformat(partner_reminder['datetime'])
    print(f"  📅 Time: {reminder_dt.strftime('%B %d, %Y at %I:%M %p')}")
    print(f"  👤 From: {partner_reminder['sender_name']}")
    print(f"  💬 Message: {partner_reminder['text']}")
    print(f"  📡 Sent: {partner_reminder['sent']}")
    
    print("\n📂 Full data structure:")
    print(json.dumps(test_data, indent=2))

if __name__ == "__main__":
    test_partner_reminders()
