import io
import json
import streamlit as st
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

st.set_page_config(layout="centered")
#st.markdown("<style>.element-container{opacity:1 !important}</style>", unsafe_allow_html=True)
state = st.session_state

st.cache()
def load_data():
    df = pd.read_csv('streamlit_data.tsv', sep='\t', encoding='utf8', index_col='Unnamed: 0')
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


df, placenames = load_data()
define_font()

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
    with open('placename_counts.json', 'r', encoding='utf8') as f:
        placename_counts = json.load(f)
    state.placename_counts = placename_counts

img = None    


st.write('Average time for news to reach Riga')

with st.form(key='my_form'):
    #with st.sidebar:

    places_input = st.multiselect(label='Choose locations (dropdown or type):',
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

