import io
import streamlit as st
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

#st.session_state

st.cache()
def load_data():
    df = pd.read_csv('streamlit_data.tsv', sep='\t', encoding='utf8', index_col='Unnamed: 0')
    return df, df.columns


st.cache()
def define_font():
    fm.fontManager.addfont('cmunorm.ttf')
    matplotlib.rcParams['font.family'] = 'CMU Concrete'


def plot():

    fig, ax = plt.subplots(figsize=(15,7))

    df[st.session_state.places_to_plot].plot(ax=ax)

    plt.xticks(ticks=range(1802,1889), labels=[str(yr) if yr%5==0 else '' for yr in range(1802,1889)], size=14)
    plt.ylabel('days', size=16)
    plt.grid(which='major', linewidth=1.2)                
    plt.legend(fontsize=14)

    st.session_state.figure = fig
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    return img


def create_filename():
    return '_'.join(st.session_state.places_to_plot) + '.png'


df, placenames = load_data()
define_font()

if 'places_to_plot' not in st.session_state:
    st.session_state.places_to_plot = ['Paris']
if 'rolling' not in st.session_state:
    st.session_state.rolling = 3
if 'figure' not in st.session_state:
    st.session_state.figure = None
if 'download_fig' not in st.session_state:
    st.session_state.download_fig = None

img = None    


st.write('Average time of news movement per year')

with st.form(key='my_form'):
    with st.sidebar:

        places_input = st.sidebar.multiselect(label='Choose locations:',
                                            options=df.columns,
                                            key='places_to_plot')

        rolling_slider = st.sidebar.slider(label='Rolling average',
                                        min_value=0,
                                        max_value=10,
                                        value=3,
                                        key='rolling')

        submit = st.form_submit_button(label='Show')

    if submit:
        img = plot()
        st.pyplot(st.session_state.figure)
    else:
        if st.session_state.figure:
            st.pyplot(st.session_state.figure)

if img:
    st.download_button(label='Download', data=img, file_name=create_filename())

