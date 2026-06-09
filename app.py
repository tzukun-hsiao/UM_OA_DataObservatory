import streamlit as st

main_page = st.Page("pages/0_welcome.py", title="Main Page", icon=None)
page_1 = st.Page("pages/1_overall.py", title="1. Temporal Trends - Publications", icon=None)
#page_2 = st.Page("pages/2_knowledge_flow.py", title="2. Visibility", icon=None)

# Set up navigation
pg = st.navigation([main_page, page_1])

# Run the selected page
pg.run()