import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import re

# Dark theme CSS
st.markdown("""
<style>
    .submit-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
        color: #e2e8f0;
        border-radius: 8px;
        margin-bottom: 2rem;
        border: 1px solid #38a169;
    }

    .form-container {
        background: #2d3748;
        padding: 2rem;
        border-radius: 8px;
        border: 1px solid #4a5568;
        margin: 1rem 0;
    }

    .info-box {
        background: #2d3748;
        border: 1px solid #63b3ed;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 1rem 0;
        border-left: 3px solid #63b3ed;
        color: #e2e8f0;
    }

    .success-box {
        background: #2d3748;
        border: 1px solid #38a169;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 3px solid #38a169;
        color: #e2e8f0;
    }

    .warning-box {
        background: #2d3748;
        border: 1px solid #ed8936;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 1rem 0;
        border-left: 3px solid #ed8936;
        color: #e2e8f0;
    }

    .campaign-output {
        background: #1a202c;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #4a5568;
    }

    .footer-tip {
        text-align: center;
        color: #a0aec0;
        padding: 1rem;
        background: #2d3748;
        border-radius: 8px;
        margin-top: 1rem;
        border: 1px solid #4a5568;
    }
</style>
""", unsafe_allow_html=True)

# Setup Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate('restaurant-data-backend-firebase-adminsdk-fbsvc-8b7fe2120f (2).json')
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Setup Gemini
genai.configure(api_key="AIzaSyA-eFWdCSUeNggTlWGzbFEA1uGtioZMQEA", transport="rest")
model = genai.GenerativeModel('gemini-1.5-flash')

# Page header
st.markdown('<div class="submit-header"><h1>✅ Submit Your Marketing Campaign</h1></div>', unsafe_allow_html=True)

# Information box
st.markdown("""
<div class="info-box">
    <h4>📝 How it works:</h4>
    <ol>
        <li>Enter your details and campaign preferences</li>
        <li>AI will generate a personalized campaign based on available inventory</li>
        <li>Your campaign will be automatically submitted for evaluation</li>
        <li>Check the leaderboard to see your AI score!</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Form container
st.markdown('<div class="form-container">', unsafe_allow_html=True)

# Current month info
current_month = datetime.now().strftime("%Y-%m")
month_name = datetime.now().strftime("%B %Y")

st.subheader(f"📅 Campaign Submission for {month_name}")

# Check if user already submitted
staff_name = st.text_input(
    "👤 Your Name",
    placeholder="Enter your full name",
    help="This will be used to identify your campaign submission"
)

if staff_name:
    campaign_doc_id = f"{staff_name}_{current_month}"
    existing = db.collection('staff_campaigns').document(campaign_doc_id).get()

    if existing.exists:
        existing_data = existing.to_dict()
        st.markdown(f"""
        <div class="warning-box">
            <h4>⚠️ Campaign Already Submitted</h4>
            <p>You have already submitted a campaign for {month_name}.</p>
            <p><strong>Submitted on:</strong> {existing_data.get('timestamp', 'Unknown date')}</p>
            <p><strong>Campaign Type:</strong> {existing_data.get('promotion_type', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Show existing campaign
        with st.expander("👀 View Your Submitted Campaign"):
            st.write("**Campaign Content:**")
            st.text_area("", existing_data.get('campaign', 'No campaign content found'), height=200, disabled=True)

            if 'ai_score' in existing_data:
                st.success(f"🎯 Your campaign has been scored: **{existing_data['ai_score']}/10**")
            else:
                st.info("⏳ Your campaign is pending AI evaluation")

        st.stop()

# Input fields
col1, col2 = st.columns(2)

with col1:
    promotion_type = st.selectbox(
        "🎯 Promotion Type",
        ["Buy 1 Get 1", "Percentage Discount", "Fixed Amount Off", "Combo Offer", "Happy Hour", "Bundle Deal",
         "Free Item", "Loyalty Reward"],
        help="Select the type of promotion you want to create"
    )

with col2:
    promotion_goal = st.selectbox(
        "🎪 Campaign Goal",
        ["Reduce Food Wastage", "Increase Daily Orders", "Launch New Dish", "Clear Excess Inventory",
         "Boost Weekend Sales", "Attract New Customers", "Increase Average Order Value"],
        help="What do you want to achieve with this campaign?"
    )

# Additional customization
with st.expander("🎨 Advanced Options (Optional)"):
    target_audience = st.selectbox(
        "👥 Target Audience",
        ["All Customers", "Regular Customers", "New Customers", "Families", "Young Adults", "Office Workers",
         "Weekend Diners"],
        help="Who should this campaign target?"
    )

    campaign_duration = st.selectbox(
        "⏰ Campaign Duration",
        ["Today Only", "This Week", "Weekend Special", "Limited Time (3 days)", "Extended (1 week)"],
        help="How long should this promotion run?"
    )

st.markdown('</div>', unsafe_allow_html=True)

# Submit button
submit_button = st.button(
    "🚀 Generate and Submit Campaign",
    type="primary",
    use_container_width=True,
    help="Click to generate your AI-powered marketing campaign"
)

if submit_button and staff_name and promotion_type and promotion_goal:
    with st.spinner('🤖 AI is crafting your perfect campaign...'):
        try:
            # Load menu data
            menu_data = [doc.to_dict() for doc in db.collection('menu').stream()]
            menu_df = pd.DataFrame(menu_data)

            # Load inventory data
            inventory_data = [doc.to_dict() for doc in db.collection('ingredient_inventory').stream()]
            inventory_df = pd.DataFrame(inventory_data)
            inventory_df['Expiry Date'] = pd.to_datetime(inventory_df['Expiry Date'], dayfirst=True)


            # Parse quantities
            def parse_quantity(qty_string):
                match = re.match(r"([\d\.]+)\s*(\w+)", str(qty_string).lower())
                return (float(match.group(1)), match.group(2)) if match else (None, None)


            def standardize_quantity(quantity, unit):
                if unit == 'kg': return quantity * 1000
                if unit == 'g': return quantity
                if unit == 'l': return quantity * 1000
                if unit == 'ml': return quantity
                if unit in ['pcs', 'piece', 'pieces']: return quantity
                return None


            parsed = inventory_df['Quantity'].apply(parse_quantity)
            inventory_df['value'] = parsed.apply(lambda x: x[0])
            inventory_df['unit'] = parsed.apply(lambda x: x[1])
            inventory_df['standardized_quantity'] = inventory_df.apply(
                lambda row: standardize_quantity(row['value'], row['unit']), axis=1
            )

            # Filter valid ingredients
            today = datetime.now()
            valid_ingredients = inventory_df[
                (inventory_df['Expiry Date'] > today) &
                (inventory_df['standardized_quantity'] > 0)
                ]
            available = valid_ingredients['Ingredient'].str.lower().tolist()

            # Filter possible dishes
            possible_dishes = []
            for _, row in menu_df.iterrows():
                required = [i.strip().lower() for i in row['ingredients']]
                if all(i in available for i in required):
                    possible_dishes.append(row['name'])

            if not possible_dishes:
                st.error(
                    "❌ No dishes can be prepared today based on current inventory. Please contact the kitchen manager.")
                st.stop()

            # Enhanced prompt for Gemini
            prompt_text = f"""
            You are a professional restaurant marketing expert creating a campaign for {month_name}.

            CAMPAIGN REQUIREMENTS:
            - Staff Member: {staff_name}
            - Promotion Type: {promotion_type}
            - Campaign Goal: {promotion_goal}
            - Target Audience: {target_audience if 'target_audience' in locals() else 'All Customers'}
            - Duration: {campaign_duration if 'campaign_duration' in locals() else 'Limited Time'}

            AVAILABLE DISHES TODAY:
            {', '.join(possible_dishes)}

            INSTRUCTIONS:
            1. Create an attractive, specific campaign using ONLY the dishes listed above
            2. Make the offer compelling with clear value proposition
            3. Include specific pricing or discount details
            4. Focus on the campaign goal: {promotion_goal}
            5. Write in an engaging, marketing-friendly tone
            6. Keep it concise but impactful (2-3 paragraphs max)
            7. Include a clear call-to-action

            Create a professional marketing campaign now:
            """

            # Generate campaign
            response = model.generate_content(prompt_text)
            campaign = response.text.strip()

            # Save to Firestore
            campaign_data = {
                "name": staff_name,
                "campaign": campaign,
                "promotion_type": promotion_type,
                "goal": promotion_goal,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "month": current_month
            }

            # Add optional fields if they exist
            if 'target_audience' in locals():
                campaign_data["target_audience"] = target_audience
            if 'campaign_duration' in locals():
                campaign_data["campaign_duration"] = campaign_duration

            db.collection("staff_campaigns").document(campaign_doc_id).set(campaign_data)

            # Success message
            st.markdown("""
            <div class="success-box">
                <h3>🎉 Campaign Successfully Submitted!</h3>
                <p>Your marketing campaign has been generated and submitted for AI evaluation.</p>
                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>Your campaign will be scored by AI within 24 hours</li>
                    <li>Check the leaderboard to see your ranking</li>
                    <li>Top performers will be recognized!</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

            # Display generated campaign
            st.markdown('<div class="campaign-output">', unsafe_allow_html=True)
            st.subheader("📢 Your Generated Campaign")
            st.markdown(f"**Campaign by:** {staff_name}")
            st.markdown(f"**Type:** {promotion_type} | **Goal:** {promotion_goal}")
            st.markdown("---")
            st.write(campaign)
            st.markdown('</div>', unsafe_allow_html=True)

            # Quick actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 View Leaderboard", use_container_width=True):
                    st.info("Navigate to the Leaderboard page to see current rankings")

            with col2:
                if st.button("📋 Copy Campaign Text", use_container_width=True):
                    st.code(campaign, language=None)

        except Exception as e:
            st.error(f"❌ Failed to generate campaign: {str(e)}")
            st.info("Please try again or contact the administrator if the problem persists.")

elif submit_button:
    st.warning("⚠️ Please fill in all required fields before submitting.")

# Footer info
st.markdown("""
<div class="footer-tip">
    <small>💡 <strong>Tip:</strong> The more specific your inputs, the better your AI-generated campaign will be!</small>
</div>
""", unsafe_allow_html=True)
