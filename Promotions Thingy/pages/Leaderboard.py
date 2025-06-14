import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from datetime import datetime
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

# Page header
st.markdown('<div class="main-header"><h1>🏆 AI Campaign Leaderboard</h1></div>', unsafe_allow_html=True)

# Get current month
current_month = datetime.now().strftime("%Y-%m")
month_name = datetime.now().strftime("%B %Y")

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
            use_container_width=True
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
            use_container_width=True
        )

    st.markdown('</div>', unsafe_allow_html=True)
