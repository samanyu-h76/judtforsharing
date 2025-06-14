import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import google.generativeai as genai
import re
from datetime import datetime
import time

# Dark theme CSS
st.markdown("""
<style>
    .admin-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
        color: #e2e8f0;
        border-radius: 8px;
        margin-bottom: 2rem;
        border: 1px solid #e53e3e;
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

    .stats-container {
        background: #2d3748;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #4a5568;
        margin: 1rem 0;
    }

    .success-container {
        background: #2d3748;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #38a169;
        border-left: 3px solid #38a169;
        margin: 1rem 0;
        color: #e2e8f0;
    }

    .info-card {
        background: #2d3748;
        padding: 2rem;
        border-radius: 8px;
        text-align: center;
        margin: 2rem 0;
        border: 1px solid #4a5568;
        color: #cbd5e0;
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
model = genai.GenerativeModel("gemini-1.5-flash")

# Page header
st.markdown('<div class="admin-header"><h1>🤖 Admin: AI Score Evaluator</h1></div>', unsafe_allow_html=True)

# Get current month info
current_month = datetime.now().strftime("%Y-%m")
month_name = datetime.now().strftime("%B %Y")

# Load campaign statistics
with st.spinner('Loading campaign statistics...'):
    docs = list(db.collection("staff_campaigns").where("month", "==", current_month).stream())
    all_campaigns = [doc.to_dict() for doc in docs]
    scored_campaigns = [doc for doc in all_campaigns if "ai_score" in doc]
    unscored_campaigns = [doc for doc in all_campaigns if "ai_score" not in doc]

# Statistics display
st.markdown('<div class="stats-container">', unsafe_allow_html=True)
st.subheader(f"📊 Campaign Statistics for {month_name}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Campaigns", len(all_campaigns))

with col2:
    st.metric("Scored", len(scored_campaigns), delta=f"{len(scored_campaigns)}")

with col3:
    st.metric("Unscored", len(unscored_campaigns),
              delta=f"-{len(unscored_campaigns)}" if len(unscored_campaigns) > 0 else "0")

with col4:
    completion_rate = (len(scored_campaigns) / len(all_campaigns) * 100) if len(all_campaigns) > 0 else 0
    st.metric("Completion", f"{completion_rate:.0f}%")

st.markdown('</div>', unsafe_allow_html=True)

# Progress bar
if len(all_campaigns) > 0:
    progress = len(scored_campaigns) / len(all_campaigns)
    st.progress(progress)
    st.caption(f"Progress: {len(scored_campaigns)}/{len(all_campaigns)} campaigns scored")

# Warning if no unscored campaigns
if len(unscored_campaigns) == 0 and len(all_campaigns) > 0:
    st.markdown("""
    <div class="success-container">
        <h4>✅ All campaigns are already scored!</h4>
        <p>All campaigns for this month have been evaluated by AI. No action needed.</p>
    </div>
    """, unsafe_allow_html=True)
elif len(all_campaigns) == 0:
    st.markdown("""
    <div class="info-card">
        <h4>📝 No campaigns submitted yet</h4>
        <p>No campaigns have been submitted for this month. Staff members need to submit campaigns first.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Show unscored campaigns
    st.subheader("⏳ Unscored Campaigns")
    for i, campaign in enumerate(unscored_campaigns[:3]):  # Show first 3
        with st.expander(f"Campaign by {campaign.get('name', 'Unknown')} - {campaign.get('promotion_type', 'N/A')}"):
            st.write(f"**Goal:** {campaign.get('goal', 'N/A')}")
            st.write(f"**Campaign Preview:** {campaign.get('campaign', 'N/A')[:200]}...")

    if len(unscored_campaigns) > 3:
        st.caption(f"... and {len(unscored_campaigns) - 3} more campaigns")

# Main action button
if len(unscored_campaigns) > 0:
    st.markdown("""
    <div class="warning-box">
        <h4>⚠️ Important Notes</h4>
        <ul>
            <li>This will score all unscored campaigns using AI</li>
            <li>The process may take a few minutes depending on the number of campaigns</li>
            <li>Already scored campaigns will be skipped automatically</li>
            <li>Scores are final and cannot be easily changed</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Run AI Scoring on Unscored Campaigns", key="score_button",
                 help="Click to start AI evaluation of all unscored campaigns"):
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        scored = 0
        skipped = 0
        failed = 0

        # Process each unscored campaign
        for i, doc in enumerate(docs):
            data = doc.to_dict()

            # Update progress
            progress = (i + 1) / len(docs)
            progress_bar.progress(progress)
            status_text.text(f"Processing campaign {i + 1} of {len(docs)}: {data.get('name', 'Unknown')}")

            if "ai_score" in data:
                skipped += 1
                continue

            campaign_text = data.get("campaign", "")
            staff = data.get("name", "Unknown")

            prompt = f"""
You are an expert in marketing strategy evaluation.
Rate the following campaign out of 10 (decimals allowed). Only output the number.
Consider creativity, clarity, focus on reducing food waste, and how persuasive it is.

Campaign:
\"\"\"
{campaign_text}
\"\"\"
"""

            try:
                with st.spinner(f'Scoring campaign by {staff}...'):
                    response = model.generate_content(prompt)
                    score_text = response.text.strip()
                    score = float(re.findall(r"[0-9]+(?:\\.[0-9]+)?", score_text)[0])
                    score = round(min(score, 10.0), 2)
                    db.collection("staff_campaigns").document(doc.id).update({"ai_score": score})
                    scored += 1

                # Small delay to avoid rate limiting
                time.sleep(0.5)

            except Exception as e:
                failed += 1
                st.error(f"Failed to score {staff}: {str(e)}")

        # Final results
        progress_bar.progress(1.0)
        status_text.text("Scoring completed!")

        # Results summary
        st.markdown('<div class="stats-container">', unsafe_allow_html=True)
        st.subheader("✅ Scoring Results")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Successfully Scored", scored, delta=f"+{scored}")
        with col2:
            st.metric("Skipped (Already Scored)", skipped)
        with col3:
            st.metric("Failed", failed, delta=f"-{failed}" if failed > 0 else "0")

        if failed == 0 and scored > 0:
            st.success(f"🎉 All {scored} campaigns scored successfully!")
        elif scored > 0:
            st.warning(f"⚠️ {scored} campaigns scored, but {failed} failed. Check error messages above.")
        else:
            st.error("❌ No campaigns were scored. Please check the error messages.")

        st.markdown('</div>', unsafe_allow_html=True)

        # Refresh button
        if st.button("🔄 Refresh Page", key="refresh"):
            st.rerun()

# Quick actions
st.markdown("---")
st.subheader("🔧 Quick Actions")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 View Leaderboard", use_container_width=True):
        st.info("Navigate to the Leaderboard page to view current rankings")

with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
