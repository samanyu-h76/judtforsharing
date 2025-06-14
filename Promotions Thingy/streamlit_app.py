import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="AI Marketing Campaigns",
    page_icon="📣",
    layout="wide"
)

# App Header
st.title("📣 AI-Generated Restaurant Marketing Campaigns")
st.markdown("Welcome to the internal AI marketing system. Use the sidebar to:")
st.markdown("- ✅ Submit your campaign")
st.markdown("- 🏆 View the leaderboard")
st.markdown("- 🤖 (Admin) Run AI scoring for all staff")

# Footer
st.markdown("---")
st.markdown("Made with 💡 by your AI team")
