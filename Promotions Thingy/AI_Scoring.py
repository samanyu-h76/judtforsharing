# rate_staff_campaigns.py

import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
import re
from datetime import datetime

# ---- STEP 1: Setup Firebase ----
if not firebase_admin._apps:
    cred = credentials.Certificate('restaurant-data-backend-firebase-adminsdk-fbsvc-bdeb44e4a8.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ---- STEP 2: Setup Gemini (REST API) ----
genai.configure(api_key="AIzaSyA-eFWdCSUeNggTlWGzbFEA1uGtioZMQEA", transport="rest")
model = genai.GenerativeModel("gemini-1.5-flash")

# ---- STEP 3: Get current month ----
current_month = datetime.now().strftime("%Y-%m")
print(f"\n📊 Rating Campaigns for Month: {current_month}\n")

# ---- STEP 4: Reset scores from previous months ----
all_docs = db.collection("staff_campaigns").stream()
for doc in all_docs:
    data = doc.to_dict()
    if data.get("month") != current_month:
        db.collection("staff_campaigns").document(doc.id).update({
            "ai_score": firestore.DELETE_FIELD
        })

# ---- STEP 5: Rate current month campaigns that are not already scored ----
current_month_docs = db.collection("staff_campaigns").where("month", "==", current_month).stream()

for doc in current_month_docs:
    data = doc.to_dict()

    if "ai_score" in data:
        print(f"⏭️ Skipping {data['name']} — already scored.")
        continue

    staff = data.get("name")
    campaign_text = data.get("campaign")

    prompt = f"""
You are an expert in marketing strategy evaluation.

Please rate the following restaurant marketing campaign out of 10, it can be in decimals too for more precision like 6.10 but no decimal for 10.
Consider creativity, clarity, relevance to reducing waste, and how convincing the offers are.

Give ONLY the score (as a number), and nothing else.

Campaign:
\"\"\"
{campaign_text}
\"\"\"
"""

    try:
        response = model.generate_content(prompt)
        score_text = response.text.strip()
        score = float(re.findall(r"[0-9]+(?:\\.[0-9]+)?", score_text)[0])
        score = round(score, 2)
        score = min(score, 10.0)

        print(f"✅ {staff}'s campaign rated: {score}/10")

        db.collection("staff_campaigns").document(doc.id).update({"ai_score": score})

    except Exception as e:
        print(f"❌ Error scoring {staff}'s campaign ({staff}): {e}")

# ---- STEP 6: Print Leaderboard Table ----
print("\n📋 Final AI Score Leaderboard:\n")

from tabulate import tabulate  # Add this import at the top if not already

leaderboard = []
rated_docs = db.collection("staff_campaigns").where("month", "==", current_month).stream()

for doc in rated_docs:
    data = doc.to_dict()
    if "ai_score" in data:
        leaderboard.append([data.get("name", "Unknown"), data.get("ai_score")])

if leaderboard:
    # Sort by highest score
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    print(tabulate(leaderboard, headers=["Staff Name", "AI Score"], tablefmt="pretty"))
else:
    print("No campaigns rated yet.")
