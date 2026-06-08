import streamlit as st

st.title("Data Observatory for UM Publications")

md_txt = '''
This app showcases the open access trends for authors associated with 
*University of Mississippi* or *University of Mississippi Medical Center*.

- Publication year spans from 2016 to 2026 May, covering 26,256 publications.
- Data collection was conducted in May 2026.
- Publication Data was collected from Dimentions.
- Citation Data was collected from OpenAlex.
'''

st.write(md_txt)