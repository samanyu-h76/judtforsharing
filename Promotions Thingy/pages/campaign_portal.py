import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import re
import time
import plotly.express as px
import plotly.graph_objects as go

# Dark theme CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
        color: #e2e8f0;
        border-radius: 8px;
        margin-bottom: 2rem;
        border: 1px solid #4a5568;
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

    .stats-container {
        background: #2d3748;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #4a5568;
        margin: 1rem 0;
    }

    .admin-section {
        background: #2d3748;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e53e3e;
        border-left: 3px solid #e53e3e;
        margin: 1rem 0;
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

    .info-card {
        background: #2d3748;
        padding: 2rem;
        border-radius: 8px;
        text-align: center;
        margin: 2rem 0;
        border: 1px solid #4a5568;
        color: #cbd5e0;
    }

    .metric-container {
        background: #2d3748;
        padding: 1.2rem;
        border-radius: 8px;
        border: 1px solid #4a5568;
        border-left: 3px solid #63b3ed;
    }

    .winner-card {
        background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
        margin: 1.5rem 0;
        border: 1px solid #63b3ed;
        color: #e2e8f0;
    }

    .download-section {
        background: #1a202c;
        padding: 1.5rem;
        border-radius: 8px;
        margin-top: 1.5rem;
        text-align: center;
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
st.markdown('<div class="main-header"><h1>🚀 Campaign Management Portal</h1></div>', unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs(["✅ Submit Campaign", "🤖 Admin Panel", "🏆 Leaderboard"])

# Get current month info (used by all tabs)
current_month = datetime.now().strftime("%Y-%m")
month_name = datetime.now().strftime("%B %Y")

# TAB 1: SUBMIT CAMPAIGN
with tab1:
    st.subheader("📝 Submit Your Marketing Campaign")

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

    st.subheader(f"📅 Campaign Submission for {month_name}")

    # Check if user already submitted
    staff_name = st.text_input(
        "👤 Your Name",
        placeholder="Enter your full name",
        help="This will be used to identify your campaign submission",
        key="staff_name_input"
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
                st.text_area("", existing_data.get('campaign', 'No campaign content found'), height=200, disabled=True,
                             key="existing_campaign_display")

                if 'ai_score' in existing_data:
                    st.success(f"🎯 Your campaign has been scored: **{existing_data['ai_score']}/10**")
                else:
                    st.info("⏳ Your campaign is pending AI evaluation")

            st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Input fields for new submission
            col1, col2 = st.columns(2)

            with col1:
                promotion_type = st.selectbox(
                    "🎯 Promotion Type",
                    ["Buy 1 Get 1", "Percentage Discount", "Fixed Amount Off", "Combo Offer", "Happy Hour",
                     "Bundle Deal", "Free Item", "Loyalty Reward"],
                    help="Select the type of promotion you want to create",
                    key="promotion_type_select"
                )

            with col2:
                promotion_goal = st.selectbox(
                    "🎪 Campaign Goal",
                    ["Reduce Food Wastage", "Increase Daily Orders", "Launch New Dish", "Clear Excess Inventory",
                     "Boost Weekend Sales", "Attract New Customers", "Increase Average Order Value"],
                    help="What do you want to achieve with this campaign?",
                    key="promotion_goal_select"
                )

            # Additional customization
            with st.expander("🎨 Advanced Options (Optional)"):
                target_audience = st.selectbox(
                    "👥 Target Audience",
                    ["All Customers", "Regular Customers", "New Customers", "Families", "Young Adults",
                     "Office Workers", "Weekend Diners"],
                    help="Who should this campaign target?",
                    key="target_audience_select"
                )

                campaign_duration = st.selectbox(
                    "⏰ Campaign Duration",
                    ["Today Only", "This Week", "Weekend Special", "Limited Time (3 days)", "Extended (1 week)"],
                    help="How long should this promotion run?",
                    key="campaign_duration_select"
                )

            st.markdown('</div>', unsafe_allow_html=True)

            # Submit button
            submit_button = st.button(
                "🚀 Generate and Submit Campaign",
                type="primary",
                use_container_width=True,
                help="Click to generate your AI-powered marketing campaign",
                key="submit_campaign_button"
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
                        else:
                            # Enhanced prompt for Gemini
                            prompt_text = f"""
                            You are a professional restaurant marketing expert creating a campaign for {month_name}.

                            CAMPAIGN REQUIREMENTS:
                            - Staff Member: {staff_name}
                            - Promotion Type: {promotion_type}
                            - Campaign Goal: {promotion_goal}
                            - Target Audience: {target_audience}
                            - Duration: {campaign_duration}

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
                                "target_audience": target_audience,
                                "campaign_duration": campaign_duration,
                                "timestamp": firestore.SERVER_TIMESTAMP,
                                "month": current_month
                            }

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
                                if st.button("📊 View Leaderboard", use_container_width=True,
                                             key="view_leaderboard_button"):
                                    st.info("Switch to the Leaderboard tab to view current rankings")

                            with col2:
                                if st.button("📋 Copy Campaign Text", use_container_width=True,
                                             key="copy_campaign_button"):
                                    st.code(campaign, language=None)

                    except Exception as e:
                        st.error(f"❌ Failed to generate campaign: {str(e)}")
                        st.info("Please try again or contact the administrator if the problem persists.")

            elif submit_button:
                st.warning("⚠️ Please fill in all required fields before submitting.")

    else:
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer info
    st.markdown("""
    <div class="footer-tip">
        <small>💡 <strong>Tip:</strong> The more specific your inputs, the better your AI-generated campaign will be!</small>
    </div>
    """, unsafe_allow_html=True)

# TAB 2: ADMIN PANEL
with tab2:
    st.markdown('<div class="admin-section">', unsafe_allow_html=True)
    st.subheader("🤖 Admin: AI Score Evaluator")
    st.markdown('</div>', unsafe_allow_html=True)

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
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Campaigns", len(all_campaigns))
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Scored", len(scored_campaigns), delta=f"{len(scored_campaigns)}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Unscored", len(unscored_campaigns),
                  delta=f"-{len(unscored_campaigns)}" if len(unscored_campaigns) > 0 else "0")
        st.markdown('</div>', unsafe_allow_html=True)

    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        completion_rate = (len(scored_campaigns) / len(all_campaigns) * 100) if len(all_campaigns) > 0 else 0
        st.metric("Completion", f"{completion_rate:.0f}%")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Progress bar
    if len(all_campaigns) > 0:
        progress = len(scored_campaigns) / len(all_campaigns)
        st.progress(progress)
        st.caption(f"Progress: {len(scored_campaigns)}/{len(all_campaigns)} campaigns scored")

    # Warning if no unscored campaigns
    if len(unscored_campaigns) == 0 and len(all_campaigns) > 0:
        st.markdown("""
        <div class="success-box">
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
            with st.expander(
                    f"Campaign by {campaign.get('name', 'Unknown')} - {campaign.get('promotion_type', 'N/A')}"):
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

        if st.button("🚀 Run AI Scoring on Unscored Campaigns", key="admin_score_button",
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
            if st.button("🔄 Refresh Page", key="admin_refresh"):
                st.rerun()

    # Quick actions
    st.markdown("---")
    st.subheader("🔧 Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📊 View Leaderboard", use_container_width=True, key="admin_view_leaderboard"):
            st.info("Switch to the Leaderboard tab to view current rankings")

    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True, key="admin_refresh_data"):
            st.rerun()

# TAB 3: LEADERBOARD
with tab3:
    st.subheader("🏆 AI Campaign Leaderboard")

    # Load campaigns with loading indicator
    with st.spinner('Loading campaign data...'):
        docs = db.collection("staff_campaigns").where("month", "==", current_month).stream()
        data = [doc.to_dict() for doc in docs if "ai_score" in doc.to_dict()]

    if not data:
        st.markdown(f"""
        <div class="info-card">
            <h3>📊 No Scored Campaigns</h3>
            <p>No campaigns have been scored for {month_name}</p>
            <p>Check back later or contact admin to run AI scoring.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Create DataFrame
        df = pd.DataFrame(data)
        df = df.sort_values(by="ai_score", ascending=False).reset_index(drop=True)
        df['rank'] = range(1, len(df) + 1)

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Total Campaigns", len(df))
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Average Score", f"{df['ai_score'].mean():.1f}/10")
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Top Score", f"{df['ai_score'].max():.1f}/10")
            st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.metric("Month", month_name)
            st.markdown('</div>', unsafe_allow_html=True)

        # Winner highlight
        top_performer = df.iloc[0]
        st.markdown(f"""
        <div class="winner-card">
            <h2>🥇 Top Performer</h2>
            <h3>{top_performer['name']}</h3>
            <p><strong>Score:</strong> {top_performer['ai_score']}/10</p>
            <p><strong>Campaign Type:</strong> {top_performer['promotion_type']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Score distribution chart
        st.subheader("📈 Score Distribution")
        fig = px.bar(
            df,
            x='name',
            y='ai_score',
            color='ai_score',
            color_continuous_scale='Blues',
            title="Campaign Scores by Staff Member"
        )
        fig.update_layout(
            xaxis_title="Staff Member",
            yaxis_title="AI Score",
            showlegend=False,
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#e2e8f0'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Leaderboard table
        st.subheader("🏅 Detailed Rankings")

        # Prepare display dataframe
        display_df = df[["rank", "name", "promotion_type", "goal", "ai_score"]].copy()
        display_df.columns = ["Rank", "Staff Name", "Promotion Type", "Goal", "Score"]
        display_df["Score"] = display_df["Score"].apply(lambda x: f"{x}/10")

        # Add rank emojis
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        display_df["Rank"] = display_df["Rank"].apply(lambda x: f"{rank_emojis.get(x, '🏅')} {x}")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # Download section
        st.markdown('<div class="download-section">', unsafe_allow_html=True)
        st.subheader("📥 Export Data")

        col1, col2 = st.columns(2)

        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                label="📊 Download Full Data (CSV)",
                data=csv,
                file_name=f"campaign_leaderboard_{current_month}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_full_data"
            )

        with col2:
            summary_data = {
                "Month": [month_name],
                "Total Campaigns": [len(df)],
                "Winner": [top_performer['name']],
                "Top Score": [f"{top_performer['ai_score']}/10"],
                "Average Score": [f"{df['ai_score'].mean():.1f}/10"]
            }
            summary_csv = pd.DataFrame(summary_data).to_csv(index=False)
            st.download_button(
                label="📋 Download Summary (CSV)",
                data=summary_csv,
                file_name=f"campaign_summary_{current_month}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_summary_data"
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # Campaign details section
        st.subheader("📝 Campaign Details")
        selected_staff = st.selectbox(
            "Select staff member to view their campaign:",
            options=df['name'].tolist(),
            key="staff_campaign_selector"
        )

        if selected_staff:
            staff_campaign = df[df['name'] == selected_staff].iloc[0]

            st.markdown('<div class="campaign-output">', unsafe_allow_html=True)
            st.markdown(f"**Campaign by:** {staff_campaign['name']}")
            st.markdown(f"**Score:** {staff_campaign['ai_score']}/10")
            st.markdown(f"**Type:** {staff_campaign['promotion_type']} | **Goal:** {staff_campaign['goal']}")
            st.markdown("---")
            st.write(staff_campaign['campaign'])
            st.markdown('</div>', unsafe_allow_html=True)
