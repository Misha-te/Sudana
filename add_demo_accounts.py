#!/usr/bin/env python3
import json

# Load existing users
with open('data/users.json', 'r') as f:
    users = json.load(f)

# Add demo accounts
demo_accounts = {
    "demo": {
        "first_name": "Demo",
        "last_name": "User",
        "username": "demo",
        "email": "demo@sudana.test",
        "password_hash": "scrypt:32768:8:1$RuLWJPp2Gx7lHcFx$687274640e214982b918cc2838776aeecd9e5d29d0d353193bcd25b2b3978159a24e601832a3c1a1750580ecc215e57420a011e813289f68dde34eb48eddeff7",
        "gender": "Other",
        "dob": "2000-01-01",
        "hometown": "Juba",
        "bio": "Welcome to Sudana! This is a demo account for testing the app.",
        "category": "Student",
        "geez": [],
        "pending_sent": [],
        "posts": [
            {
                "id": "demo-post-1",
                "text": "Welcome to Sudana! Feel free to explore and test all features. Use reactions, create posts, and discover the community.",
                "created_at": "2026-07-11T12:00:00",
                "created_label": "Jul 11, 2026 at 12:00 PM",
                "visibility": "public",
                "shared_with": [],
                "media_filename": None,
                "media_type": None,
                "likes": [],
                "reactions": {}
            }
        ],
        "photo_permission": False
    },
    "test": {
        "first_name": "Test",
        "last_name": "Account",
        "username": "test",
        "email": "test@sudana.test",
        "password_hash": "scrypt:32768:8:1$FGt8U0q2GFWMP24V$a608e77d3e67d29082eba40ffa86f7728e7337e03bb9cc40d41fffaa4032455494c266202dac4fa9038d02c8f4ec4fdf5ab8841d72b03cfa58b55140342a1a48",
        "gender": "Female",
        "dob": "1998-05-15",
        "hometown": "Khartoum",
        "bio": "Testing Sudana features",
        "category": "Artist",
        "geez": [],
        "pending_sent": [],
        "posts": [
            {
                "id": "test-post-1",
                "text": "Great platform for connecting with the South Sudanese community!",
                "created_at": "2026-07-10T15:30:00",
                "created_label": "Jul 10, 2026 at 3:30 PM",
                "visibility": "public",
                "shared_with": [],
                "media_filename": None,
                "media_type": None,
                "likes": [],
                "reactions": {}
            }
        ],
        "photo_permission": False
    },
    "visitor": {
        "first_name": "Visitor",
        "last_name": "Guest",
        "username": "visitor",
        "email": "visitor@sudana.test",
        "password_hash": "scrypt:32768:8:1$RvB0NmfDrD2kWLuM$6a121fca147b69473339f51997e8f5064ec622e5cba2c597e033aa50fa976fde8001568b8cd9ca6267ecd1c23da3bc4426996cb7918af9b3a855c33bc5e64eb0",
        "gender": "Prefer not to say",
        "dob": "1995-03-20",
        "hometown": "Nairobi",
        "bio": "Exploring the Sudana community",
        "category": "Other",
        "geez": [],
        "pending_sent": [],
        "posts": [],
        "photo_permission": False
    }
}

users.update(demo_accounts)

# Save
with open('data/users.json', 'w') as f:
    json.dump(users, f, indent=2)

print("Demo accounts added successfully!")
print("Accounts created:")
print("  demo / demo123456")
print("  test / test123456")
print("  visitor / visitor123456")
