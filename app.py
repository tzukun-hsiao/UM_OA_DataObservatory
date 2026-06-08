import streamlit as st

main_page = st.Page("pages/0_welcome.py", title="Main Page", icon="🎈")
page_1 = st.Page("pages/1_overall.py", title="Temporal Trends - Publications", icon="❄️")
page_2 = st.Page("pages/2_knowledge_flow.py", title="Visibility", icon="🧠")

# Set up navigation
pg = st.navigation([main_page, page_1, page_2])

# Run the selected page
pg.run()