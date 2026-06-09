import io
import requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
from github import Github, Auth


@st.cache_data
def load_data(file_name):
    auth = Auth.Token(st.secrets["GITHUB_TOKEN"])
    g = Github(auth=auth)
    repo = g.get_repo(st.secrets["DATA_REPO"])

    file = repo.get_contents(f'OA_DataObservatory/{file_name}')

    response = requests.get(
        file.download_url,
        headers={"Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}"}
    )
    response.raise_for_status()

    return pd.read_csv(io.BytesIO(response.content))

def gini(input_vals):
    x_vals = np.array(input_vals)
    # values must be non-negative
    x_vals = x_vals[x_vals >= 0]
    if np.sum(x_vals) == 0:
        return 0
    x_vals = np.sort(x_vals)
    n = len(x_vals)
    idx = np.arange(1, n + 1)
    gini_value = np.sum((2 * idx - n - 1) * x_vals) / (n * np.sum(x_vals))
    
    return gini_value

pubs = load_data(file_name='UM_publications_SelectedCols.csv')
pubs = pubs.rename(columns={'Publication ID': 'cited_PublicationID', 
                            'PubYear': 'cited_PubYear'})

cits = load_data(file_name='citing_articles_kept_cols.csv')
cits = cits.rename(columns={'Publication ID': 'citing_PublicationID', 
                            'PubYear': 'citing_PubYear'})
cits = cits.drop_duplicates()

kf_field = load_data(file_name='citation_pairs_kf_SelectedCols.csv')
kf_field = kf_field.merge(pubs, how='left')
kf_field['Is_OA'] = 'OA'
kf_field.loc[kf_field['Open Access']=='Closed', 'Is_OA'] = 'Closed'
kf_field['cited_ResearchField'] = kf_field['cited_ResearchFields_mjr'].str.split('|')
kf_field = kf_field.explode('cited_ResearchField')
kf_field['citing_ResearchField'] = kf_field['citing_ResearchFields_mjr'].str.split('|')
kf_field = kf_field.explode('citing_ResearchField')
kf_field = kf_field.drop_duplicates()
kf_field['cited_ResearchField_OA'] = kf_field['cited_ResearchField'] + ', ' + kf_field['Is_OA']
#kf_field['citing_ResearchField_OA'] = kf_field['citing_ResearchField'] + ', ' + kf_field['Is_OA']
kf_field = kf_field.merge(cits, how='left')
kf_field = kf_field.loc[kf_field['citing_PubYear'] >= kf_field['cited_PubYear']]

cit_pair_country = load_data(file_name='citation_pair_countries.csv')
#cit_pair_country['cited_ResearchField'] = cit_pair_country['cited_ResearchFields_mjr'].str.split('|')
#cit_pair_country = cit_pair_country.explode('cited_ResearchField')

# Sankey diagram
md_txt = '''
## How UM’s Open Access and Closed Publications Were Cited in the Literature
'''
st.markdown(md_txt)

md_txt = f"""
### Discipline Level Citation Flows
"""
st.markdown(md_txt)

md_txt = """
Figure below shows how knowledge in UM publications might diffuse to other disciplines, as indicated by citation linkages.
A citation link indicates a potential knowledge flow from the cited article to the citing article.
In the figure, UM publications are the cited articles and are grouped by their disciplines.
The width of lines are proportional to citation counts.
The higher the citation count is, the wider the line is.

Using the dropdown menus below, you can choose to visualize data for the discipline(s) and 
article type of your choice.
"""
st.write(md_txt)


kf_field_g = kf_field.groupby(['cited_ResearchField'])[['cited_PublicationID']].nunique()
kf_field_g = kf_field_g.sort_values(by=['cited_PublicationID'], ascending=False)

selected_fields = st.multiselect("Select disciplines:",
                                 options=kf_field_g.index.tolist(), 
                                 key="field_selection1")
article_type_options = pubs['Document Type'].dropna().unique().tolist()
article_type = st.selectbox(label='Select an article type:', options=article_type_options, 
                            index=None, placeholder='Select an article type:', 
                            key="article_type_selection1")

df_data_pub_ids = None
if len(selected_fields) == 0:
    selected_fields = kf_field_g.head(5).index.tolist()
    if article_type is None:
        article_type_str = 'All articles'
        df_data = kf_field.loc[kf_field['cited_ResearchField'].isin(selected_fields)]
        df_data_pub_ids = df_data['cited_PublicationID'].unique().tolist()
    else:
        article_type_str = article_type
        df_data = kf_field.loc[kf_field['cited_ResearchField'].isin(selected_fields)]
        df_data = df_data.loc[df_data['Document Type'] == article_type]
        df_data_pub_ids = df_data['cited_PublicationID'].unique().tolist()
else:
    if article_type is None:
        article_type_str = 'All articles'
        df_data = kf_field.loc[kf_field['cited_ResearchField'].isin(selected_fields)]
        df_data_pub_ids = df_data['cited_PublicationID'].unique().tolist()
    else:
        article_type_str = article_type
        df_data = kf_field.loc[kf_field['cited_ResearchField'].isin(selected_fields)]
        df_data = df_data.loc[df_data['Document Type'] == article_type]
        df_data_pub_ids = df_data['cited_PublicationID'].unique().tolist()

# df_tbl_out = [['Discipline', 'Closed Access/Open Access',
#                'Number of Citing Disciplines', 'Number of Publications', 'Number of Citations', 
#                'Evenness']]
# for um_pub_field in selected_fields:
#     um_selected = df_data.loc[df_data['cited_ResearchField']==um_pub_field]
#     oa_types = um_selected['Is_OA'].unique().tolist()
#     oa_types.sort()
#     for oa_type in oa_types:
#         um_selected2 = um_selected.loc[um_selected['Is_OA']==oa_type]
#         n_pubs = um_selected2['cited_PublicationID'].nunique()
#         n_cits = um_selected2['citing_PublicationID'].nunique()

#         um_selected_g = um_selected2.groupby('citing_ResearchField')[['citing_PublicationID']].nunique()
#         n_citing_disc = len(um_selected_g)
#         gini_cit = gini(um_selected_g['citing_PublicationID'].tolist())

#         row = [um_pub_field, oa_type, n_citing_disc, n_pubs, n_cits, gini_cit]
#         df_tbl_out.append(row)

# df_tbl_out = pd.DataFrame(df_tbl_out[1:], columns=df_tbl_out[0])
# df_tbl_out['Evenness'] = df_tbl_out['Evenness'].round(2)

selected_fields_str = ', '.join(selected_fields)

tot_or_avg = st.selectbox(label='Select how citations are calculated:', 
                          options=['Total number of citations', 'Average citations per article'], 
                          index=0, key='total_or_average')

md_txt = """
- Total number of citations: The total number of citation received by articles in a discipline.
- Average citations per article: The total number of citations divided by the number of articles in the cited discipline.
"""
st.caption(md_txt)

md_txt = f"""
- Disciplines selected: {selected_fields_str}  
- Article type selected: {article_type_str}
"""
st.markdown(md_txt)

if tot_or_avg == 'Average citations per article':
    df_plt = df_data.groupby(['cited_ResearchField', 'cited_ResearchField_OA',
                              'citing_ResearchField']).agg({'citing_PublicationID': 'count', 
                                                            'cited_PublicationID': 'nunique'})
    df_plt = df_plt.reset_index()
    df_plt = df_plt.rename(columns={'citing_PublicationID': 'citation_count_raw', 
                                    'cited_PublicationID': 'num_cited_pubs'})
    df_plt['citation_count'] = df_plt['citation_count_raw'] / df_plt['num_cited_pubs']

else:
    df_plt = df_data.groupby(['cited_ResearchField', 'cited_ResearchField_OA',
                              'citing_ResearchField'])[['citing_PublicationID']].count().reset_index()
    df_plt = df_plt.rename(columns={'citing_PublicationID': 'citation_count'})

df_plt['Is_OA'] = df_plt['cited_ResearchField_OA'].str.split(', ').str[-1]

left_nodes = selected_fields
middle_nodes = []
for field in selected_fields:
    field_open = field + ', OA'
    field_closed = field + ', Closed'
    middle_nodes += [field_open, field_closed]
right_nodes = df_plt["citing_ResearchField"].unique().tolist()

left_internal = ['l_' + x for x in left_nodes]
middle_internal = ['m_' + x for x in middle_nodes]
right_internal = ['r_' + x for x in right_nodes]

labels_internal = left_internal + middle_internal + right_internal
labels_display = left_nodes + middle_nodes + right_nodes

label_to_id = {label: i for i, label in enumerate(labels_internal)}

# Right set of links
source1 = df_plt['cited_ResearchField_OA'].apply(lambda x: label_to_id['m_' + x])
target1 = df_plt['citing_ResearchField'].apply(lambda x: label_to_id['r_' + x])
value1 = df_plt['citation_count'] 

# Left set of links
df_plt_g = df_plt.groupby(['cited_ResearchField', 
                           'cited_ResearchField_OA']).agg({'citation_count': 'sum', 
                                                           'citing_ResearchField': 'nunique'})
df_plt_g = df_plt_g.reset_index()
df_plt_g['Is_OA'] = df_plt_g['cited_ResearchField_OA'].str.split(', ').str[-1]
 
source2 = df_plt_g['cited_ResearchField'].apply(lambda x: label_to_id['l_' + x])
target2 = df_plt_g['cited_ResearchField_OA'].apply(lambda x: label_to_id['m_' + x])
value2 = df_plt_g["citation_count"] 

source = list(source1) + list(source2)
target = list(target1) + list(target2)
value = list(value1) + list(value2)

link_colors1 = []
for oa_label in df_plt['cited_ResearchField_OA'].tolist():
    if oa_label[-2:] == 'OA':
        link_clr = "rgba(0,150,0,0.4)"
        link_colors1.append(link_clr)
    else:
        link_clr = "rgba(100,100,100,0.4)"
        link_colors1.append(link_clr)

link_colors2 = []
for oa_label in df_plt_g['cited_ResearchField_OA'].tolist():
    if oa_label[-2:] == 'OA':
        link_clr = "rgba(0,150,0,0.4)"
        link_colors2.append(link_clr)
    else:
        link_clr = "rgba(100,100,100,0.4)"
        link_colors2.append(link_clr)

palette = px.colors.qualitative.Set1
field_color_map = {}
for i, field in enumerate(list(set(left_nodes + right_nodes))):
    rgb = palette[i % len(palette)]
    rgb = rgb.replace("rgb(", "").replace(")", "") # convert "rgb(102,194,165)" → "102,194,165"
    field_color_map[field] = rgb

node_colors = []
for label in labels_display:
    if ", OA" in label:
        field = label.replace(", OA", "")
        rgb = field_color_map.get(field, "150,150,150")
        color = f"rgba({rgb},0.9)"
    elif ", Closed" in label:
        field = label.replace(", Closed", "")
        rgb = field_color_map.get(field, "150,150,150")
        color = f"rgba({rgb},0.6)"
    else:
        rgb = field_color_map.get(label, "150,150,150")
        color = f"rgba({rgb},0.6)"
    node_colors.append(color)

hover_text1 = [
    (
        f"Knowledge Flow Diresction:{cited_field} → {citing_filed}<br>"
        #f"Cited field: {cited_field}<br>"
        #f"Citing field: {citing_filed}<br>"
        f"OA status of UM publications: {oa_type}<br>"
        f"Citations: {cnt/1000:.1f}k"
    )
    for oa_type, cited_field, citing_filed, cnt in zip(
        df_plt['Is_OA'],
        df_plt['cited_ResearchField'],
        df_plt['citing_ResearchField'],
        df_plt['citation_count']
    )
]

hover_text2 = [
    f"OA status of UM publications: {oa_type}<br>Citations: {cnt/1000:.1f}k"
    for oa_type, cnt in zip(
        df_plt_g['Is_OA'],
        df_plt_g['citation_count']
    )
]

hover_text = hover_text1 + hover_text2

y_left = [0.05 + i * 0.9 / (len(left_internal)) for i in range(len(left_internal))]
y_middle = [0.05 + i * 0.9 / (len(middle_internal) -1) for i in range(len(middle_internal))]
y_right = [
    0.02 + i * 0.96 / max(len(right_nodes) - 1, 1)
    for i in range(len(right_nodes))
]
y_positions = y_left + y_middle + y_right
x_positions = [0.01] * len(left_internal) + [0.28] * len(middle_internal) + [0.99] * len(right_internal)

fig = go.Figure(data=[go.Sankey(
    arrangement="snap",
    node=dict(
        pad=15, 
        thickness=15, 
        x = x_positions,
        y = y_positions,
        label = labels_display,
        color = node_colors,
        hovertemplate="<extra></extra>"
    ),
    link=dict(
        #arrowlen=15,
        source = source,
        target = target,
        value = value,
        color = link_colors1 + link_colors2,
        customdata=hover_text,
        hovertemplate="%{customdata}<extra></extra>"
    )
)])

fig.add_annotation(
    x=0.01,
    y=1.05,
    text="<b>Disciplines of the cited UM Publications</b>",
    showarrow=False,
    xref="paper",
    yref="paper",
    font=dict(size=18)
)

fig.add_annotation(
    x=0.99,
    y=1.05,
    text="<b>Disciplines of the Citing Articles</b>",
    showarrow=False,
    xref="paper",
    yref="paper",
    font=dict(size=18)
)

fig.update_layout(
    height=800,
    #margin=dict(l=20, r=100, t=10, b=10)
)

st.plotly_chart(fig, width='content')
cap_txt = '''
- The width of lines are proportional to citation counts. The higher the citation count is, the wider the line is.
- Green lines indicate citations received by open access articles.
- Gray lines indicates citations received by closed access articles
'''
st.caption(cap_txt)

md_txt = """
The table below shows the number of unique disciplines that cite a selected discipline.
"""
#st.write(md_txt)
#st.write(df_tbl_out)

md_txt = '''
- *Evenness* measures how evenly citations were distributed across disciplines.  
- Evenness values were calculated using Gini index.
The values ranges from 0 to 1. (0 = perfect equality; 1 = prefect inequality)
'''
#st.caption(md_txt)


# Map
md_txt = f"""
#### Countries Citing UM publications 
"""
st.markdown(md_txt)

md_txt = f'''
The two figures below show how knowledge from UM publications diffused to other countries. 
Darker colors indicate a higher proportion of citations from a given country. 
Compared with open-access articles, citations to non open-access articles are more 
concentrated in the United States and China. This pattern suggests that open-access 
articles may reach a broader international audience.
'''
st.markdown(md_txt)

md_txt = f"""
- Disciplines selected: {selected_fields_str}  
- Article type selected: {article_type_str}
"""
st.markdown(md_txt)

df_data_country = cit_pair_country.loc[cit_pair_country['cited_PublicationID'].isin(df_data_pub_ids)]
#st.write(df_data_country.head())
df_data_country_g = df_data_country.groupby(['citing_country', 
                                             'Is_OA'])[['citing_PublicationID']].nunique()
df_data_country_g = df_data_country_g.rename(columns={'citing_PublicationID': 'cit_count'})
#df_data_country_g['log_cit_count'] = np.log2(df_data_country_g['cit_count'])
df_data_country_g = df_data_country_g.reset_index()
#st.write(df_data_country_g.head())

country_open = df_data_country_g.loc[df_data_country_g['Is_OA']=='OA'].copy()
country_open['pct_cit_count'] = country_open['cit_count']/country_open['cit_count'].sum()*100
country_open['pct_cit_count'] = country_open['pct_cit_count'].round(2)

country_closed = df_data_country_g.loc[df_data_country_g['Is_OA']=='Closed'].copy()
country_closed['pct_cit_count'] = country_closed['cit_count']/country_closed['cit_count'].sum()*100
country_closed['pct_cit_count'] = country_closed['pct_cit_count'].round(2)

country_cit_pct_max = max([country_open['pct_cit_count'].max(), country_closed['pct_cit_count'].max()])
country_cit_pct_min = min([country_open['pct_cit_count'].min(), country_closed['pct_cit_count'].min()])

country_open_fig = px.choropleth(
    country_open,
    locations="citing_country",
    locationmode="country names",
    #locationmode="ISO-3",
    color="pct_cit_count", 
    title='(a) Open Access Articles',
    color_continuous_scale="OrRd",
    range_color=(country_cit_pct_min, country_cit_pct_max), 
    hover_data={'citing_country': True, 'pct_cit_count': ':.1f'}
)

country_closed_fig = px.choropleth(
    country_closed,
    locations="citing_country",
    locationmode="country names",
    #locationmode="ISO-3",
    color="pct_cit_count",
    title='(b) Closed Access Articles',
    color_continuous_scale="OrRd",
    range_color=(country_cit_pct_min, country_cit_pct_max),
    hover_data={'citing_country': True, 'pct_cit_count': ':.1f'}
)

for country_fig in [country_open_fig, country_closed_fig]:
    country_fig.update_geos(
        showland=True,
        landcolor="#808080",
        bgcolor="#000000",
        domain=dict(y=[0.05, 0.95])
    )
    country_fig.update_layout(
        height=600, 
        margin=dict(t=30, b=10),
        coloraxis_colorbar=dict(
            orientation="h",
            y=-0.15,      # move below plot
            x=0.5,        # center horizontally
            xanchor="center",
            len=0.95,      # length of colorbar
            title = 'Percentage of citations'
        ), 
        title=dict(
            y=0.9
        )
    )
    country_fig.update_traces(
        hovertemplate=
            "Country: %{location}<br>" +
            "Percentag of Citations: %{z:.1f}%<br>" +
            "<extra></extra>"
    )

st.plotly_chart(country_open_fig, width='stretch')
st.plotly_chart(country_closed_fig, width='stretch')    


# Article Field Citation Ratio (FCR)
md_txt = f"""
#### Distribution of Articles' Field-Normalized Citation Metric Scores
"""
st.markdown(md_txt)

md_txt = f"""
Figure below presents distribution of Field Citation Ratio (FCR) for the selected disciplines.
FCR is a age and discipline normalized citation indicator.
It shows the relative citation performance of an article among articles published in the 
same year and in the same discipline.
The FCR is normalized to 1.0. An FCR value of more than 1.0 shows that the publication has 
a higher than average number of citations, comparing to other articles published in the same 
year and in the same discipline.
- Disciplines selected: {selected_fields_str}  
- Article type selected: {article_type_str}
"""
st.markdown(md_txt)

#df_tbl_per_pub = [['PID', 'Discipline', 'Closed Access/Open Access',
#                   'Number of Citing Disciplines', 'FCR']]
df_tbl_per_pub = df_data.groupby(['cited_PublicationID', 'cited_ResearchField', 'Is_OA', 
                                  'FCR'])[['citing_ResearchField']].nunique().reset_index()
df_tbl_per_pub = df_tbl_per_pub.rename(columns={'citing_ResearchField': 'n_citing_ResearchField'})
df_plt = df_tbl_per_pub.loc[~df_tbl_per_pub['FCR'].isna()]
#st.write(df_plt.shape[0])
df_plt = df_plt.loc[df_plt['FCR']<=50]
#st.write(df_plt.shape[0])

fig, ax = plt.subplots(figsize=(15, 6))
sns.boxplot(data=df_plt, 
            x="cited_ResearchField", y="FCR", hue="Is_OA", 
            fill=False, gap=.1,
            palette={"OA": "#009600", "Closed": "#646464"},
            #log_scale= 2,
            #whis = (0.0, 1.0),
            ax=ax)

#ax.set_ylim(0, 100)
ax.set_ylabel('Field Citation Ratio (FCR)', size=16)
ax.legend(ncol=2)
st.write(fig)
cap_txt = '''
- In consideration of readability, articles with FCR > 50 were omitted in this plot.
'''
st.caption(cap_txt)


# Annual citations
md_txt = f"""
#### Annual Citations per Article, by Publication Year and OA Status
"""
st.markdown(md_txt)

md_txt = f"""
Figure below presents the annual citations per article for open-access and non open-access articles.
The vertical axis shows the publication year of the articles, and the horizontal axis shows the citation year. 
Each bar represents the average number of citations received per article in a given citation year.
Regarless of open access or not, anuual citations generally peak around 2-4 years after publication. 
This pattern reflects the citation lifecycle of scholarly articles, in which research takes time to be discovered 
and incorporated into later studies.
However, throughout the citation lifecycle, open-access articles generally receive more 
citations per article than non open-access articles.
"""
st.markdown(md_txt)

annual_data = kf_field.loc[kf_field['Document Type']=='Research Article']

article_field = st.selectbox(label='Select a discipline:', 
                             options=kf_field_g.index.tolist(), 
                             index=None, placeholder='Select a discipline:', 
                             key="article_field_selection")
if article_field is not None:
    annual_data = annual_data.loc[annual_data['citing_ResearchField'] == article_field]
    article_field_str = article_field
else:
    article_field_str = 'All articles'

annual_data = annual_data.loc[annual_data['cited_PubYear'] < 2025]
annual_data = annual_data.groupby(['cited_PubYear', 'citing_PubYear', 
                                   'Is_OA']).agg({'citing_PublicationID': 'count', 
                                                  'cited_PublicationID': 'nunique'}).reset_index()
annual_data['citation_per_paper'] = annual_data['citing_PublicationID'] / annual_data['cited_PublicationID']
#annual_data = annual_data.sort_values(["cited_PubYear", "citing_PubYear"])
#st.write(annual_data)

year_order = sorted(annual_data["citing_PubYear"].unique(), key=int)
year_order = [str(int(y)) for y in year_order]
fig = px.bar(
    annual_data,
    x="citing_PubYear",
    y="citation_per_paper",
    color="Is_OA",
    color_discrete_map={'OA': 'rgb(0,150,0)', 'Closed': 'rgb(100,100,100)'},
    facet_row="cited_PubYear",   # one row per publication year
    barmode="group",
    title=f"Showing results for {article_field_str}",
    category_orders={"citing_PubYear": year_order},
    hover_data={'citation_per_paper': ':.1f', 'citing_PubYear': True, 'Is_OA': True}
)
fig.update_traces(
    hovertemplate=
    "Citation year: %{x}<br>" +
    "Citations per article: %{y:.1f}<br>" +
    "OA Type: %{fullData.name}<br>" +
    "<extra></extra>"
)

fig.for_each_annotation(
    lambda a: a.update(
        text=a.text.replace("cited_PubYear=", "PY="),
        textangle=0
    )
)

#fig.update_xaxes(type="category")
fig.update_yaxes(title_text="")
fig.update_xaxes(
    type="category",
    categoryorder="array",
    categoryarray=year_order,
)

fig.update_layout(
    height=95 * annual_data["cited_PubYear"].nunique(),
    legend_title_text="OA Status",
    xaxis_title='Year',
    legend=dict(orientation="h", y=1.07, x=1.05, xanchor="right"),
    margin=dict(t=120, r=100)
    #margin=dict(l=20, r=100, t=40, b=40)
)
fig.add_annotation(
    text="Citation Per Paper",
    xref="paper",
    yref="paper",
    x=-0.08,
    y=0.5,
    textangle=-90,
    showarrow=False,
    font=dict(size=14)
)
st.write(fig)

#st.write(year_order)
#st.write(annual_data["citing_PubYear"].unique())
#st.write(sorted(annual_data["citing_PubYear"].astype(str).unique()))
#st.write(annual_data)