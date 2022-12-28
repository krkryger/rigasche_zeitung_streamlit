import io
import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from PIL import Image

st.set_page_config(layout="centered")
state = st.session_state


if 'places_to_plot' not in state:
    state.places_to_plot = ['Paris']
if 'rolling' not in state:
    state.rolling = 1
if 'display_counts' not in state:
    state.display_counts = False
if 'figure' not in state:
    state.figure = None
if 'download_fig' not in state:
    state.download_fig = None
if 'placename_counts' not in state:
    with open('data/placename_counts.json', 'r', encoding='utf8') as f:
        placename_counts = json.load(f)
    state.placename_counts = placename_counts

if 'scatterplot_place' not in state:
    state.scatterplot_place = 'Paris'
if 'jitter' not in state:
    state.jitter = True
if 'display_season' not in state:
    state.display_season = False
if 'cutoff' not in state:
    state.cutoff = 100
if 'scatterplot_figure' not in state:
    state.scatterplot_figure = None



st.cache()
def load_data():
    df = pd.read_csv('data/streamlit_data.tsv', sep='\t', encoding='utf8', index_col='Unnamed: 0')
    return df, df.columns

st.cache()
def load_hierarchy():
    hierarchy = pd.read_csv('data/topics/topic_hierarchy.tsv', sep='\t', encoding='utf8')
    return hierarchy

st.cache()
def define_font():
    fm.fontManager.addfont('cmunorm.ttf')
    matplotlib.rcParams['font.family'] = 'CMU Concrete'


def plot():

    fig = plt.figure(figsize=(15,7))

    for name in state.places_to_plot:
        label = f'{name} ({state.placename_counts[name]} entries)' if state.display_counts else name
        df[name].rolling(state.rolling, min_periods=1).mean().reindex(range(1802,1889)).plot(label=label)

    plt.xticks(ticks=range(1802,1889), labels=[str(yr) if yr%5==0 else '' for yr in range(1802,1889)], size=14)
    plt.yticks(size=14)
    plt.ylabel('days', size=16)
    plt.grid(which='major', linewidth=1.2)                
    plt.legend(fontsize=14, loc='upper right',
               ncol=1 if len(state.places_to_plot) < 11 else 2)

    state.figure = fig
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    return img


def create_filename():
    return '_'.join(state.places_to_plot) + '.png'


def jitter_dots(dots):
    offsets = dots.get_offsets()
    jittered_offsets = offsets
    jittered_offsets[:, 0] += np.random.uniform(-0.5, 0.5, offsets.shape[0])
    jittered_offsets[:, 1] += np.random.uniform(-0.5, 0.5, offsets.shape[0])
    dots.set_offsets(jittered_offsets)


def plot_speed_distribution(place=state.scatterplot_place, jitter=state.jitter, cutoff=state.cutoff, display_season=state.display_season):
    
    fig = plt.figure(figsize=(15,7))
    
    data = pd.read_csv(f'data/places/{place}.tsv', sep='\t', encoding='utf8')
    if cutoff:
        data = data.loc[data.delta <= cutoff]

    dots = plt.scatter(x=data.year, y=data.delta, s=5, label=place, alpha=0.6)
    if jitter:
        jitter_dots(dots)

    if display_season:
        data.loc[data.season=='s'].groupby('year')['delta'].mean().rolling(3).mean().reindex(range(1802,1889)).plot(color='red', alpha=0.7, label='Apr-Sep')
        data.loc[data.season=='w'].groupby('year')['delta'].mean().rolling(3).mean().reindex(range(1802,1889)).plot(color='blue', alpha=0.7, label='Oct-Mar')
        
    plt.xticks(ticks=range(1802,1889), labels=[str(yr) if yr%5==0 else '' for yr in range(1802,1889)], size=14)
    plt.yticks(size=14)
    plt.ylabel('days', size=16)
    plt.grid(which='major', linewidth=1.2)
    plt.legend(fontsize=14, loc='upper right')

    state.scatterplot_figure = fig
    img_scatter = io.BytesIO()
    plt.savefig(img_scatter, format='png', bbox_inches='tight')
    return img_scatter


def find_parents(top, hierarchy):
    
    family = hierarchy.loc[hierarchy.isin([top]).any(axis=1)].values
    
    topic_level = np.where(family==top)[1][0]
    
    if topic_level == 0:
        parent = None
        children = list(set(family[:, 1]))
        
    elif topic_level == family.shape[1]-1:
        parent = list(set(family[:, topic_level-1]))
        children = None
        
    else:
        parent = list(set(family[:, topic_level-1]))
        children = list(set(family[:, topic_level+1]))
                  
    return parent, children    



df, placenames = load_data()
hierarchy = load_hierarchy()
define_font()

img = None   
img_scatter = None


########################### BODY OF THE APP

st.title('Communication speed in the 19th century')
st.markdown("""This page lets you explore the speed of communication in printed media as reflected in the 19th century newspaper _Rigasche Zeitung_.
The data is acquired from the digitized collections of the Latvian National Library and spans from 1802 to 1888 (with 1882 missing).
In the 19th century, news from abroad were accompanied by the date and place of origin of the information at hand.
Using a complex regular expression, this metadata has been extracted from the newspaper and cleaned, resulting in more than 200 000 entries containing (among other information), the place of origin of the news and its date.
Subtracting the origin date from the date of publication gives us the delay experienced by readers in Riga.""")


st.header('Average news speed')
st.markdown("""This widget allows you to compare the average delay in information between different locations.
The averages are calculated for each year, using entries with a delay less than 120 days.
The general trend shows a strong convergeance, most explicitly seen in the 1860s when Riga was connected to the telegraph network.""")

with st.form(key='plot1'):

    places_input = st.multiselect(label='Choose locations:',
                                        options=df.columns,
                                        key='places_to_plot',
                                        help='Tip: you can also start typing in the box to find a location faster')

    rolling_slider = st.slider(label='Rolling average',
                                    min_value=1,
                                    max_value=10,
                                    key='rolling',
                                    help= 'Smooths the curve by displaying the average of multiple years. "1" means no smoothing.')

    display_counts = st.checkbox(label='Display number of entries',
                                    value=False,
                                    key='display_counts',
                                    help='Check this box to see the number of news originating from each place (during the whole period)')
    
    submit = st.form_submit_button(label='Show')


if submit:
    img = plot()
    st.pyplot(state.figure)
else:
    if state.figure:
        st.pyplot(state.figure)

if img:
    st.download_button(label='Download', data=img, file_name=create_filename())


st.text('\n\n\n\n')
st.header('Detailed news speed')
st.markdown("""This graph lets you observe the speed of news with individual datapoints, thus offering a more detailed view than the averages presented above.""")

with st.form(key='plot2'):

    scatterplot_place = st.selectbox(label='Choose location:',
                                        options=df.columns,
                                        key='scatterplot_place',
                                        help='Tip: you can also start typing in the box to find a location faster')

    cutoff = st.slider(label='Cutoff',
                                    min_value=30,
                                    max_value=100,
                                    step=10,
                                    key='cutoff',
                                    help= 'Maximum value to be displayed')

    jitter = st.checkbox(label='Jitter dots',
                            key='jitter',
                            help='Uncheck this box to stop jittering (nudging) the dots4')

    display_season = st.checkbox(label='Display seasons',
                                key='display_season',
                                help='Distinguish between winter and summer')                            
    
    submit_scatter = st.form_submit_button(label='Show')


if submit_scatter:
    img_scatter = plot_speed_distribution()
    st.pyplot(state.scatterplot_figure)
else:
    if state.scatterplot_figure:
        st.pyplot(state.scatterplot_figure)

if img_scatter:
    st.download_button(label='Download', data=img_scatter, file_name=f'{state.scatterplot_place}.png')



st.header('Topics')
st.markdown("""The articles following the places and dates can also be modeled thematically.
Using top2vec ([D. Angelov, 2020](https://top2vec.readthedocs.io/en/stable/Top2Vec.html#usage), about 200 000 segments of text were divided into 352 topics.
With Top2Vec, it is possible to reduce the number of topics by merging them into each other by order of similarity.
This widget allows you to choose the preferred level of detail (30, 40 50 or 60 topics).
Each topic is presented in the form of a wordcloud where the size of words is indicative of how relevant/unique they are to the chosen topic.
You can also examine the temporal distribution of the topic, as well as the main article headings it appears under.
Further down, you can read example texts for each topic, which are ordered by their centrality in the topic.""")

reductions = [0] + [int(folder.split('_')[1]) for folder in os.listdir(os.getcwd()+'/data/topics') if 'reduction' in folder]

#reductions = [0, 12, 36, 72]

topic_reduction = st.radio(label='Number of topics',
                               options=reductions[1:],
                               key='reduction',
                               help= 'Choose the number of topics to reduce the original 351 topics to. Choosing a lower number means that the topics are more general; higher number results in more detailed topics.')

topic = st.slider(label='Choose a topic:',
                  min_value=sum(reductions[:reductions.index(topic_reduction)])+1,
                  max_value=sum(reductions[:reductions.index(topic_reduction)])+topic_reduction)
    
#submit_reduction = st.form_submit_button(label='Show')

if topic_reduction:
    
    with open(f'data/topics/reduction_{str(topic_reduction)}/sizes.json', 'r', encoding='utf8') as f:
        sizes = json.load(f)


if topic:

    st.subheader(f'Topic {topic}')

    st.markdown(f'**Size: {sizes[topic-1-sum(reductions[:reductions.index(topic_reduction)])]} segments**')

    parent, children = find_parents(topic, hierarchy)
    if parent is not None:
        st.markdown(f'Parent topic{"s" if len(parent) > 1 else ""}: {", ".join([str(p) for p in parent])}')
    if children is not None:
        st.markdown(f'Child topic{"s" if len(children) > 1 else ""}: {", ".join([str(c) for c in children])}')

    wordcloud = Image.open(f'data/topics/reduction_{str(topic_reduction)}/wordclouds/topic_{str(topic-1)}.png')
    st.image(wordcloud)

    statistics = Image.open(f'data/topics/reduction_{str(topic_reduction)}/statistics/topic_{str(topic-1)}.png')
    st.image(statistics)

    with open(f'data/topics/reduction_{str(topic_reduction)}/examples/examples_{str(topic-1)}.json', 'r', encoding='utf8') as f:
        topic_examples = json.load(f)
        #current_example = 0

    st.markdown('#### Examples')

    tabs = st.tabs([str(i)+'    ' for i in range(1, len(topic_examples)+1)])

    for tab, ex in zip(tabs, range(20)):

        with tab:

            example_data = topic_examples[ex]
            date = example_data['date']
            heading = example_data['heading']
            text = example_data['text']
            text = text.replace('\n\n\t', '\n\n')
            text = text.replace('\n\n', '_\n\n_')

            st.markdown(f"##### {heading}")
            st.markdown(f"**{date}**")
            st.markdown(f"\n_{text.strip().lstrip()}_")



    



