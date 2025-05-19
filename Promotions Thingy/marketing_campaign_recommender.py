# Import libraries
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import re

# Step 1: Setup Firebase safely
if not firebase_admin._apps:
    cred = credentials.Certificate('restaurant-data-backend-firebase-adminsdk-fbsvc-bdeb44e4a8.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Step 2: Get Staff Name and Setup
staff_name = input("Enter your name: ")
current_month = datetime.now().strftime("%Y-%m")
campaign_doc_id = f"{staff_name}_{current_month}"

# Optional: Clear old campaigns from previous months
campaigns = db.collection('staff_campaigns').stream()
for doc in campaigns:
    data = doc.to_dict()
    if data.get('month') != current_month:
        db.collection('staff_campaigns').document(doc.id).delete()

# Check if campaign already exists for this user/month
existing = db.collection('staff_campaigns').document(campaign_doc_id).get()
if existing.exists:
    print("❌ You have already submitted a campaign this month.")
    exit()

# Step 3: Read Menu Collection
menu_ref = db.collection('menu')
menu_docs = menu_ref.stream()
menu_data = [doc.to_dict() for doc in menu_docs]
menu_df = pd.DataFrame(menu_data)
print("✅ Menu Data Loaded")
print(menu_df)

# Step 4: Read Inventory Collection
inventory_ref = db.collection('ingredient_inventory')
inventory_docs = inventory_ref.stream()
inventory_data = [doc.to_dict() for doc in inventory_docs]
inventory_df = pd.DataFrame(inventory_data)
print("✅ Inventory Data Loaded")
print(inventory_df)

# Step 5: Preprocess Inventory
today = datetime.now()
inventory_df['Expiry Date'] = pd.to_datetime(inventory_df['Expiry Date'], dayfirst=True)

def parse_quantity(qty_string):
    if isinstance(qty_string, str):
        match = re.match(r"([\d\.]+)\s*(\w+)", qty_string.lower())
        if match:
            return float(match.group(1)), match.group(2)
    return None, None

def standardize_quantity(quantity, unit):
    if unit in ['kg']: return quantity * 1000
    elif unit in ['g']: return quantity
    elif unit in ['l']: return quantity * 1000
    elif unit in ['ml']: return quantity
    elif unit in ['pcs', 'piece', 'pieces']: return quantity
    else: return None

parsed_quantities = inventory_df['Quantity'].apply(parse_quantity)
inventory_df['quantity_value'] = parsed_quantities.apply(lambda x: x[0])
inventory_df['quantity_unit'] = parsed_quantities.apply(lambda x: x[1])
inventory_df['standardized_quantity'] = inventory_df.apply(
    lambda row: standardize_quantity(row['quantity_value'], row['quantity_unit']),
    axis=1
)

valid_ingredients_df = inventory_df[
    (inventory_df['Expiry Date'] > today) &
    (inventory_df['standardized_quantity'] > 0)
]
available_ingredients = valid_ingredients_df['Ingredient'].str.lower().tolist()

# Step 6: Find Dishes that Can be Made
possible_dishes = []
for idx, row in menu_df.iterrows():
    required_ingredients = [i.strip().lower() for i in row['ingredients'].split(',')]
    if all(ingredient in available_ingredients for ingredient in required_ingredients):
        possible_dishes.append(row['name'])

print(f"\n✅ Dishes that can be prepared today:")
print(possible_dishes)

# Step 7: Setup Gemini API (use REST to avoid gRPC conflicts)
genai.configure(api_key="AIzaSyA-eFWdCSUeNggTlWGzbFEA1uGtioZMQEA", transport="rest")

# Step 8: Ask for Promotion Info
promotion_type = input("Enter promotion type (e.g., Buy 1 Get 1, Discount, Combo Offer): ")
promotion_goal = input("Enter promotion goal (e.g., Reduce wastage, Increase orders, Launch new dish): ")

# Step 9: Create Prompt
prompt_text = f"""
You are a professional restaurant marketing expert.

ONLY promote dishes from this list today:
{', '.join(possible_dishes)}

Promotion type requested: {promotion_type}
Promotion goal: {promotion_goal}

Only use the dishes from the provided list.
Make offers very attractive, specific, creative, and include discounts, combos, or happy hour deals depending on the promotion type.
Also focus on selling ingredients that are expiring within next 2 days if possible.
"""

# Step 10: Generate Marketing Campaign
model = genai.GenerativeModel('models/gemini-1.5-flash')
response = model.generate_content(prompt_text)
generated_campaign = response.text

print("\n✅ AI-Generated Marketing Campaign:")
print(generated_campaign)

# Step 11: Save to Firestore
campaign_record = {
    "name": staff_name,
    "campaign": generated_campaign,
    "promotion_type": promotion_type,
    "goal": promotion_goal,
    "timestamp": firestore.SERVER_TIMESTAMP,
    "month": current_month
}

db.collection("staff_campaigns").document(campaign_doc_id).set(campaign_record)
print("✅ Campaign saved successfully to Firestore.")

