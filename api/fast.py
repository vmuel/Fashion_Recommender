import numpy as np
import pandas as pd
from PIL import Image
from io import BytesIO
import base64

from api.helpers import itemrecs, bestindex, is_tunnel, non_tunnel_items, contains_strings
from api.helpers import get_gcp_user_data, get_gcp_df_data, save_gcp_user_data

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from requests_html import HTMLSession
from fastapi.responses import StreamingResponse

from google.cloud import storage
import pickle
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "credentials.json"


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def test():
    return {"status": "OK"}

@app.get("/recommend")
#Makes one recommendation from a user's profile and their feedback on the previous recommendation
def reco(userID, response, sizes, categories, gender, budget, is_filter):

    #Reformating filtering data
    sizes = sizes.split('_')
    categories = categories.split('_')
    budget = int(budget)

    #Loading user and items data from cloud storage
    #Pado: dataframe where the columns = items liked and rows = closest recommendations for each like
    #Histo: Dictionnary where keys = id of liked item and values = number of recommendations derived from said item
    #Lstorage: list of all the recommendations made
    #Oob_ratio (out of the box ratio) = once every x recommendation, the algo makes a random recommendation
        #The goal is to test the user's appetite for styles too different to be recommended from the current likes
    pado, histo, lstorage, oob_ratio = get_gcp_user_data(userID)
    print("User data loaded")
    print(pado.shape)
    print(f"Out of the box ratio: {oob_ratio}")
    gender = str(lstorage[0])
    tdfc, resnet, custom = get_gcp_df_data(gender)
    print("Clothing database loaded")

    #Filtering data
    if is_filter == 'y':
        #Possibility to filter data based on budget, size and category
        #Not available with the current onboarding process but works on theory
        tdfc = tdfc[tdfc['Budget'] == budget]
        searchable_sizes = contains_strings(sizes)
        #tdfs = tdfb[tdfb['Clean_sizes']].str.contains(searchable_sizes)
        tdfc = tdfc[tdfc.Clean_sizes.str.contains(searchable_sizes)]
        searchable_categories = contains_strings(categories)
        #tdfc = tdfs[tdfs["Category"]].str.contains(searchable_categories)
        tdfc = tdfc[tdfc.Category.str.contains(searchable_categories)]
        selected_indexes = list(tdfc.index)
        resnet = resnet[selected_indexes]
        custom = custom[selected_indexes]
        non_tunnel_items_list = non_tunnel_items(resnet, 0.9)
        print(tdfc.shape)
    else:
        selected_indexes = list(tdfc.index)
        non_tunnel_items_list = non_tunnel_items(resnet, 0.9)

    #The non-tunnel_items_list is a list of items that excludes items too similar from one another
    #Example: white shirts, blue jeans... Those items are too similar and not excluding them could result
    #In the algorithm being stuck recommending only white shirts if the user has liked a white shirt in the past

    #Recommendation
    #Tunnel_rate is the variable that defines the dimension of a tunnel
    #A tunnel is when the algorithm is stuck making bad recommendations based on items liked by the user
    #Here, a tunnel is when for x item likeds, the algorithm has generated 3x bad recommendations
    tunnel_rate = 3
    counter = (len(lstorage) - 1)

    if response == 'n':
        reco, histo, lstorage = bestindex(pado, histo, lstorage, counter, oob_ratio, resnet, custom, tdfc, non_tunnel_items_list, selected_indexes)
    if response == 'y':
        reco = int(lstorage[-1])
        pado[reco] = pd.Series(itemrecs(reco, resnet, custom, tdfc))
        histo[reco] = 0
        reco, histo, lstorage = bestindex(pado, histo, lstorage, counter, oob_ratio, resnet, custom, tdfc, non_tunnel_items_list, selected_indexes)

    #Defines the oob_ratio for the next recommendation based on whether the recommendations are in a 'tunnel' or not
    oob_ratio = is_tunnel(pado, histo, tunnel_rate)

    #Extracting recommendation data
    iTitle = tdfc.loc[reco]['Title']
    iBrand = tdfc.loc[reco]['Brand']
    iDescription = tdfc.loc[reco]['Description']
    iSize = tdfc.loc[reco]['Sizing']
    iPrice = tdfc.loc[reco]['Price']
    iSale = tdfc.loc[reco]['Sale']
    iLink = tdfc.loc[reco]['Product_link']
    iCutoff = tdfc.loc[reco]['Cutoff']
    #iImg2 = tdf.loc[reco]['Image2']
    #iImg3 = tdf.loc[reco]['Image3']

    session = HTMLSession()
    response1 = session.get(iCutoff)
    print(f'Index of recommendation: {reco}')

    uimg1 = Image.open(BytesIO(response1.content))
    uimg1 = np.array(uimg1)

    print(f'Image shape: {uimg1.shape}')
    uimg1shape = uimg1.shape
    uimg1 = uimg1.astype('uint8')
    uimg1 = base64.b64encode(uimg1)
    # Prepare image for POST request
    uimg1 = uimg1.decode('utf-8').replace("'", '"')

    #Save the updated user data with the last recommendation
    print(lstorage)
    status = save_gcp_user_data(userID, pado, histo, lstorage, oob_ratio)
    print(status)

    api_dict = {'Title':iTitle,
                'Brand':iBrand,
                'Description':iDescription,
                'Size':iSize,
                'Price':iPrice,
                'Sale':iSale,
                'Product_link':iLink,
                'Cutoff_img':uimg1,
                'Cutoff_shape':uimg1shape}

    del tdfc, resnet, custom
    return api_dict


@app.get('/register')
def register(choices, gender):
    #Receive the onbarding data as in the 'x,y,z' format and change it to a list [x,y,z]
    str_choices = choices.split(",")
    int_choices = [int(i) for i in str_choices]
    #Load the number of users
    client = storage.Client()
    bucket = client.get_bucket('...')
    users_numbers_path =  "Data/Data/Users/users_number.pickle"
    users_number_blob = bucket.blob(users_numbers_path)
    users_number_pickle = users_number_blob.download_as_string()
    users_number_dic = pickle.loads(users_number_pickle)
    #Load clothing data to make the first recommendations based on the users choices
    tdf, resnet_embeddings, custom_embeddings = get_gcp_df_data(gender)
    #transform choices into pado, histo, storage and oob_ratio
    lstorage = [str(gender), int_choices[0]]
    pado = pd.DataFrame(itemrecs(int_choices[0], resnet_embeddings, custom_embeddings, tdf), columns=[int_choices[0]])
    histo = {int_choices[0]:0}
    oob_number = 7
    for i in int_choices[1:]:
        lstorage.append(i)
        listint = pd.DataFrame(itemrecs(i, resnet_embeddings, custom_embeddings, tdf), columns=[i])
        pado[i] = listint
        histo[i] = 0
    print(f"pado shape: {pado.shape}")
    print(f"storage shape: {len(lstorage)}")
    print(f"histo shape: {len(histo)}")
    print(f"histo: {histo}")

    #Save new user data
    new_number = users_number_dic['users_number'] + 1
    userID = "ID" + str(new_number)
    #Use function to save data
    status = save_gcp_user_data(userID, pado, histo, lstorage, oob_number)

    #Adjust new number of users
    new_number_dic = {'users_number': new_number }
    new_number_blob = bucket.blob(users_numbers_path)
    new_number_pickle = pickle.dumps(new_number_dic)
    new_number_blob.upload_from_string(new_number_pickle)

    print(f'user {new_number} created')
    del tdf, resnet_embeddings, custom_embeddings
    del users_number_blob, users_number_pickle, new_number_blob, new_number_pickle

    return userID, status
