import streamlit as st
from PIL import Image
import matplotlib.pyplot as plt

import requests
import json
import base64
import numpy as np
from io import BytesIO
from app_helpers import load_recommendation


#------

st.set_page_config(
    page_title="Fashion Recommender",  # => Quick reference - Streamlit
    page_icon="👕",
    layout="centered",  # wide
    initial_sidebar_state="auto")  # collapsed

st.title('Online Fashion Recommender')
#st.header('Content-based recommender that uses')
st.markdown('''
Content-based algorithm that draws from users feedback to make recommendations
''')

weight_list = ['iTitle', 'iBrand', 'iDescription', 'iSize', 'iPrice', 'iSale', 'iLink', 'iCutoff_img', 'iCutoff_shape']

#-----Profile initialization
if 'initialization' not in st.session_state:

    st.markdown('''
    First, please select a gender
    ''')

    option = st.selectbox(
        'You are interested in clothing for...',
        ('Menswear', 'Womenswear'))

    st.markdown('''
    For each category of clothing, please select at least one item that suits your tastes.
    Don't worry if no item fits your style, this is just to give the algorithm something to start with
    ''')

    #image = Image.open('Onboarding/Men/Coats/Menswear_Coats_row_1_col_0.webp')
    #st.image(image, caption='Sunrise by the mountains')

    #----Coats

    st.header('Coats & Jackets')

    path = "Onboarding/" + option + "/Coats/"

    for i in range(0,3): # number of rows in table! = 3
        cols = st.columns(3) # number of columns in each row! = 3
        # first column of the ith row
        cols[0].image(path + option + '_Coats_row_%i_col_0.webp' %i, use_column_width=True, caption= f'{i+1}A')
        cols[1].image(path + option + '_Coats_row_%i_col_1.webp' %i, use_column_width=True, caption= f'{i+1}B')
        cols[2].image(path + option + '_Coats_row_%i_col_2.webp' %i, use_column_width=True, caption= f'{i+1}C')

    coats_input = st.multiselect(
        'What are your favorite items?',
        ['1A', '1B', '1C', '2A', '2B', '2C', '3A', '3B', '3C'],
        key='coats')

    Menswear_coats_dic = {'1A':119, '1B':885, '1C':329, '2A':886, '2B':1166, '2C':117, '3A':29, '3B':519, '3C':557}
    Womenswear_coats_dic = {'1A':817, '2B': 126, '3A': 1194, '1B': 3488, '2B': 1200, '3B': 337, '1C': 1678, '2C': 1005, '3C': 202}
    coats_id = []
    if option == 'Menswear':
        coats_dic = Menswear_coats_dic
    if option == 'Womenswear':
        coats_dic = Womenswear_coats_dic
    for i in coats_input:
        coats_id.append(coats_dic[i])

    #----Bottoms

    st.header('Bottoms')

    path = "Onboarding/" + option + "/Pants/"

    for i in range(0,3): # number of rows in table! = 3
        cols = st.columns(3) # number of columns in each row! = 3
        # first column of the ith row
        cols[0].image(path + option + '_Pants_row_%i_col_0.webp' %i, use_column_width=True, caption= f'{i+1}A')
        cols[1].image(path + option + '_Pants_row_%i_col_1.webp' %i, use_column_width=True, caption= f'{i+1}B')
        cols[2].image(path + option + '_Pants_row_%i_col_2.webp' %i, use_column_width=True, caption= f'{i+1}C')

    pants_input = st.multiselect(
        'What are your favorite items?',
        ['1A', '1B', '1C', '2A', '2B', '2C', '3A', '3B', '3C'],
        key='pants')

    Menswear_pants_dic = {'1A':137, '1B':812, '1C':1326, '2A':122, '2B':2890, '2C':3336, '3A':529, '3B':190, '3C':256}
    Womenswear_pants_dic = {'1A': 1195, '2A': 32, '3A': 3454, '1B': 815, '2B': 790, '3B': 417, '1C': 258, '2C': 731, '3C': 2333}
    pants_id = []
    if option == 'Menswear':
        pants_dic = Menswear_pants_dic
    if option == 'Womenswear':
        pants_dic = Womenswear_pants_dic
    for i in pants_input:
        pants_id.append(pants_dic[i])

    #----Tops

    st.header('Tops')

    path = "Onboarding/" + option + "/Tops/"

    for i in range(0,3): # number of rows in table! = 3
        cols = st.columns(3) # number of columns in each row! = 3
        # first column of the ith row
        cols[0].image(path + option + '_Tops_row_%i_col_0.webp' %i, use_column_width=True, caption= f'{i+1}A')
        cols[1].image(path + option + '_Tops_row_%i_col_1.webp' %i, use_column_width=True, caption= f'{i+1}B')
        cols[2].image(path + option + '_Tops_row_%i_col_2.webp' %i, use_column_width=True, caption= f'{i+1}C')

    tops_input = st.multiselect(
        'What are your favorite items?',
        ['1A', '1B', '1C', '2A', '2B', '2C', '3A', '3B', '3C'],
        key='tops')

    Menswear_tops_dic = {'1A':763, '1B':237, '1C':240, '2A':748, '2B':711, '2C':320, '3A':480, '3B':33, '3C':225}
    Womenswear_tops_dic = {'1A': 107, '2A': 812, '3A': 2793, '1B': 2684, '2B': 342, '3B': 890, '1C': 492, '2C': 264, '3C': 601}
    tops_id = []
    if option == 'Menswear':
        tops_dic = Menswear_tops_dic
    if option == 'Womenswear':
        tops_dic = Womenswear_tops_dic
    for i in tops_input:
        tops_id.append(tops_dic[i])

    #----Sweaters

    st.header('Sweaters')

    path = "Onboarding/" + option + "/Sweaters/"

    for i in range(0,3): # number of rows in your table! = 3
        cols = st.columns(3) # number of columns in each row! = 3
        # first column of the ith row
        cols[0].image(path + option + '_Sweaters_row_%i_col_0.webp' %i, use_column_width=True, caption= f'{i+1}A')
        cols[1].image(path + option + '_Sweaters_row_%i_col_1.webp' %i, use_column_width=True, caption= f'{i+1}B')
        cols[2].image(path + option + '_Sweaters_row_%i_col_2.webp' %i, use_column_width=True, caption= f'{i+1}C')

    sweaters_input = st.multiselect(
        'What are your favorite items?',
        ['1A', '1B', '1C', '2A', '2B', '2C', '3A', '3B', '3C'],
        key='sweaters')

    Menswear_sweaters_dic = {'1A':205, '1B':204, '1C':255, '2A':43, '2B':1418, '2C':530, '3A':2169, '3B':1721, '3C':1171}
    Womenswear_sweaters_dic = {'1A': 1228, '2A': 949, '3A':847, '1B': 134, '2B': 560, '3B': 1569, '1C': 2745, '2C': 1366, '3C': 1244}
    sweaters_id = []
    if option == 'Menswear':
        sweaters_dic = Menswear_sweaters_dic
    if option == 'Womenswear':
        sweaters_dic = Womenswear_sweaters_dic
    for i in sweaters_input:
        sweaters_id.append(sweaters_dic[i])

    #-----Initialize

    #Preparing the registering account API call
    choices_list = coats_id + tops_id + pants_id + sweaters_id
    reverse_choices = [str(i) for i in choices_list]
    choices = ",".join(reverse_choices)

    gender_dic = {'Menswear':'M', 'Womenswear':'W'}
    gender = gender_dic[option]

    if st.button("Start", key='start'):
        if coats_input == [] or pants_input == [] or tops_input == [] or sweaters_input == []:
            st.write("For each category, please select at least one item")
        else:
            st.session_state['initialization'] = 'done'
            st.write('Analysing personal preferences…')
            url = 'https://tokfin-ux2qpjxuga-nn.a.run.app/'
            #Initialize account
            register_params = {
                'choices': choices,
                'gender':gender}
            register_response = requests.get(url + "register", params=register_params).json()
            userID = register_response[0]
            if register_response[1] == "recommendation_data_saved":
                st.write("Profile created!")
                st.session_state['userID'] = userID
                st.session_state['gender'] = gender

            #Get first reco
            iTitle, iBrand, iDescription, iSize, iPrice, iSale, iLink, iCutoff_img, iCutoff_shape = load_recommendation(userID, gender, 'y')
            st.session_state['iCutoff_img'] = iCutoff_img
            st.session_state['iCutoff_shape'] = iCutoff_shape
            st.session_state['iTitle'] = iTitle
            st.session_state['iBrand'] = iBrand
            st.session_state['iSize'] = iSize
            st.session_state['iSale'] = iSale
            st.session_state['iPrice'] = iPrice
            st.session_state['iDescription'] = iDescription
            st.session_state['iLink'] = iLink

            if st.button("Open Recommendations", key='open'):
                st.write("Opening the recommendations...")

else:
    st.header("Recommendations")
    st.markdown('''
                Clicking the *Like* and *Dislike* buttons allow the algorithm to make better recommendations.

                Please wait until the app is done running before either liking or dislking an item.
                ''')
    #Display recommendation image
    img = base64.b64decode(bytes(st.session_state['iCutoff_img'], 'utf-8'))
    img = np.frombuffer(img, dtype='uint8')
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.imshow(img.reshape(st.session_state['iCutoff_shape']))
    ax.axis('off')
    st.pyplot(fig)
    #Recommendation details
    st.subheader(st.session_state['iTitle'])
    st.caption(st.session_state['iBrand'])
    st.caption(f"Available in : {st.session_state['iSize']}")
    if st.session_state['iSale'] == "No_sale":
        st.text(st.session_state['iPrice'])
    else:
        st.text(f"Was {st.session_state['iPrice']} but is now on sale at {st.session_state['iSale']}")
    st.write(st.session_state['iDescription'])
    st.write(st.session_state['iLink'])


    #Options
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    like = col2.button("Like", key='like')
    dislike = col5.button("Dislike", key='dislike')

    if like:

        #Delete session state
        for key in weight_list:
            del st.session_state[key]

        iTitle, iBrand, iDescription, iSize, iPrice, iSale, iLink, iCutoff_img, iCutoff_shape = load_recommendation(st.session_state['userID'], st.session_state['gender'], 'y')
        st.session_state['iCutoff_img'] = iCutoff_img
        st.session_state['iCutoff_shape'] = iCutoff_shape
        st.session_state['iTitle'] = iTitle
        st.session_state['iBrand'] = iBrand
        st.session_state['iSize'] = iSize
        st.session_state['iSale'] = iSale
        st.session_state['iPrice'] = iPrice
        st.session_state['iDescription'] = iDescription
        st.session_state['iLink'] = iLink
    if dislike:

        #Delete session state
        for key in weight_list:
            del st.session_state[key]

        iTitle, iBrand, iDescription, iSize, iPrice, iSale, iLink, iCutoff_img, iCutoff_shape = load_recommendation(st.session_state['userID'], st.session_state['gender'], 'n')
        st.session_state['iCutoff_img'] = iCutoff_img
        st.session_state['iCutoff_shape'] = iCutoff_shape
        st.session_state['iTitle'] = iTitle
        st.session_state['iBrand'] = iBrand
        st.session_state['iSize'] = iSize
        st.session_state['iSale'] = iSale
        st.session_state['iPrice'] = iPrice
        st.session_state['iDescription'] = iDescription
        st.session_state['iLink'] = iLink


st.markdown("---")
glink='[@vmuel](https://github.com/vmuel)'
st.markdown("Github: " + glink,unsafe_allow_html=True)
llink='[@vincentmuel](https://www.linkedin.com/in/vincent-muel/)'
st.markdown("LinkedIn: " + llink,unsafe_allow_html=True)
