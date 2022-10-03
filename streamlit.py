import io
import json
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

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
if 'cutoff' not in state:
    state.cutoff = 100
if 'scatterplot_figure' not in state:
    state.scatterplot_figure = None



st.cache()
def load_data():
    df = pd.read_csv('data/streamlit_data.tsv', sep='\t', encoding='utf8', index_col='Unnamed: 0')
    return df, df.columns


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


def plot_speed_distribution(place=state.scatterplot_place, jitter=state.jitter, cutoff=state.cutoff):
    
    fig = plt.figure(figsize=(15,7))
    
    data = pd.read_csv(f'data/places/{place}.tsv', sep='\t', encoding='utf8')
    if cutoff:
        data = data.loc[data.delta <= cutoff]
    
    dots = plt.scatter(x=data.year, y=data.delta, s=3, label=place, alpha=0.6)
    if jitter:
        jitter_dots(dots)
        
    plt.xticks(ticks=range(1802,1889), labels=[str(yr) if yr%5==0 else '' for yr in range(1802,1889)], size=14)
    plt.yticks(size=14)
    plt.ylabel('days', size=16)
    plt.grid(which='major', linewidth=1.2)
    plt.legend(fontsize=14, loc='upper right')

    state.scatterplot_figure = fig
    img_scatter = io.BytesIO()
    plt.savefig(img_scatter, format='png', bbox_inches='tight')
    return img_scatter



df, placenames = load_data()
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
                                    max_value=150,
                                    key='cutoff',
                                    help= 'Maximum value to be displayed')

    jitter = st.checkbox(label='Jitter dots',
                            key='jitter',
                            value=state.jitter,
                            help='Uncheck this box to stop jittering (nudging) the dots4')
    
    submit_scatter = st.form_submit_button(label='Show')


if submit_scatter:
    img_scatter = plot_speed_distribution()
    st.pyplot(state.scatterplot_figure)
else:
    if state.scatterplot_figure:
        st.pyplot(state.scatterplot_figure)

if img_scatter:
    st.download_button(label='Download', data=img_scatter, file_name=f'{state.scatterplot_place}.png')

