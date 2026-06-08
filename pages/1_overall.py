import io
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from github import Github, Auth

@st.cache_data
def load_data(file_name):
    auth = Auth.Token(st.secrets["GITHUB_TOKEN"])
    g = Github(auth=auth)
    repo = g.get_repo("tzukun-hsiao/DataMisc")

    file = repo.get_contents(f'OA_DataObservatory/{file_name}')

    response = requests.get(
        file.download_url,
        headers={"Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}"}
    )
    response.raise_for_status()

    return pd.read_csv(io.BytesIO(response.content))


pubs = load_data(file_name='UM_publications_SelectedCols.csv')
pubs['Is_OA'] = 'Closed'
pubs.loc[pubs['Open Access'] != 'Closed', 'Is_OA'] = 'Open Access' 
pubs['Open Access2'] = pubs['Open Access']
pubs['OA Type'] = pubs['Open Access2'].str.replace('All OA; ', 'OA: ')

# Stacked bar chart - Yearly Number of OA articles
md_txt = '''
## Number and Shares of Closed/OA Publications in Each Year
'''
st.markdown(md_txt)

md_txt = f"""
From 2016 to 2025, the share of open access publications increased from 43.6% to 56.2%.
Research articles and review articles both showed substantial growth in open access publishing in the past ten years.
The proportion of open access research articles continued to increase between 2016 and 2024, reaching a peak of 70.0% in 2024.
"""
st.markdown(md_txt)

# selection of an article type
article_type_options = pubs['Document Type'].dropna().unique().tolist()
article_type = st.selectbox(label='Select an article type:', options=article_type_options, 
                            index=None, placeholder='Select an article type:',
                            key="article_type_selection1")

if article_type is None:
    df_prep = pubs
    pub_type_selected = 'All articles'
else:
    df_prep = pubs.loc[pubs['Document Type']==article_type]
    pub_type_selected = article_type

oa_yr_count = df_prep.groupby(['PubYear', 'Is_OA', 'OA Type'])[['Publication ID']].count().reset_index()
oa_yr_count = oa_yr_count.rename(columns={'Publication ID': 'Publication Count'})
oa_yr_count = oa_yr_count.sort_values(by=['PubYear', 'Is_OA'], ascending=[True, True])
oa_yr_count['%'] = oa_yr_count['Publication Count'] / oa_yr_count.groupby(['PubYear'])['Publication Count'].transform('sum') * 100
oa_yr_count['%'] = oa_yr_count['%'].round(1)

df_oa_or_not = df_prep.groupby(['PubYear', 'Is_OA',])[['Publication ID']].count().reset_index()
df_oa_or_not = df_oa_or_not.rename(columns={'Publication ID': 'Publication Count'})
df_oa_or_not['%'] = df_oa_or_not['Publication Count'] / df_oa_or_not.groupby(['PubYear'])['Publication Count'].transform('sum') * 100
df_oa_or_not['%'] = df_oa_or_not['%'].round(1)

fig = px.bar(data_frame=oa_yr_count, x='Is_OA', y='Publication Count', facet_col='PubYear',
             color='OA Type', 
             labels={"PubYear": "PY"},
             title=f'Yearly Number of Closed/OA Publications; Article type: {pub_type_selected}',
             color_discrete_map= {'Closed': '#847996', 'OA: Green': '#66A3A0', 
                                  'OA: Gold': '#CCA63E', 'OA: Bronze': '#715B1E', 'OA: Hybrid': '#486BC4'})
fig.update_xaxes(title_text=None)
fig

st.text('\n\n')
if st.checkbox('Show OA types in table below:'):
    st.dataframe(oa_yr_count.set_index('PubYear'))
else:
    st.dataframe(df_oa_or_not)


# Stacked bar chart - Most Open Disciplines
md_txt = '''
## Shares of Closed/OA Articles by Disciplines
'''
st.markdown(md_txt)

md_txt = '''
Overall, half of the 22 disciplines have more than 50% of their research articles available as open access.
*Physical Sciences* has the highest share of open access research articles, with 96.3% available as open access. 
*Biological Sciences*, *Law and Legal Studies*, and *Mathematical Sciences* also have open access shares above 75%.
'''
st.markdown(md_txt)


pubs['dicsipline'] = pubs['Fields of Research (ANZSRC 2020)'].str.split('; ').str[0]
pubs['dicsipline'] = pubs['dicsipline'].str[3:]

# selection of an article type
article_type_options = pubs['Document Type'].dropna().unique().tolist()
article_type = st.selectbox(label='Select an article type:', options=article_type_options, 
                            index=None, placeholder='Select an article type:', 
                            key="article_type_selection2")

if article_type is None:
    selected_df = pubs
    article_type_str = 'All articles'
else:
    selected_df = pubs.loc[pubs['Document Type']==article_type]
    article_type_str = article_type

disc_size = selected_df.groupby(['dicsipline'])[['Publication ID']].count()
disc_top = disc_size.sort_values(by=['Publication ID'], ascending=False).head(1).index.tolist()[0]

openness = selected_df.groupby(['dicsipline', 'Is_OA'])[['Publication ID']].count().reset_index()
openness = openness.rename(columns={'Publication ID': 'Publication Count'})
openness['pct'] = openness['Publication Count'] / openness.groupby(['dicsipline'])['Publication Count'].transform('sum') * 100

#st.write(openness.loc[openness['pct']>50])

line_df = selected_df.groupby(['dicsipline', 'PubYear', 'Is_OA'])[['Publication ID']].count().reset_index()
line_df = line_df.rename(columns={'Publication ID': 'Publication Count'})
line_df['dicsipline_pct'] = line_df['Publication Count'] / line_df.groupby(['dicsipline', 'PubYear'])['Publication Count'].transform('sum') * 100

desired_order = ['Open Access', 'Closed']
bar_fig = px.bar(openness, x='dicsipline', y='pct', color='Is_OA', barmode='stack', 
                 category_orders={'Is_OA': desired_order},
                 labels={'pct': '% of Publications'}, 
                 title=f'Openness of Publications<br>Article type: {article_type_str}')
bar_fig.update_layout(legend=dict(orientation="h", y=1.65, x=1,xanchor="right"),
                      margin=dict(t=150))
bar_fig.update_xaxes(tickmode='array', tickvals=openness['dicsipline'].unique(),)

col1, col2 = st.columns(2)
with col1:
    event = st.plotly_chart(
        bar_fig,
        key="bar",
        on_select="rerun",
        selection_mode="points"
    )

selected_discipline = None

if event.selection.points:
    selected_discipline = event.selection.points[0]["x"]

if selected_discipline is None:
    selected_discipline = disc_top

filtered_line_df = line_df[line_df["dicsipline"] == selected_discipline]

line_fig = px.line(filtered_line_df.sort_values("PubYear"),
                   x="PubYear", y="Publication Count", color="Is_OA", markers=True,
                   title='Number of Closed/OA Articles in:<br>' + selected_discipline)

line_fig.update_layout(legend=dict(orientation="h", y=1.2, x=1,xanchor="right"),
                       margin=dict(t=150))

with col2:
    st.plotly_chart(line_fig, key="line")
