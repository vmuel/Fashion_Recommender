import numpy as np
import pandas as pd
#Handling the embeddings for recommendation
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import DBSCAN
import random2 as random
#Cloud
from google.cloud import storage
import io
import pickle

import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "credentials.json"

#----- Functions

def itemrecs(num_item, fresnet_embeds, fcustom_embeds, ftdf):
    #For a given item, returns the list of every other items ranked how similar in style they are
    #Style similarity is derived from the minmax-scaled cosine similarity between the ResNet and custom model
    #embeddings of the item and every other items in the dataset
    img_space = pd.DataFrame(fresnet_embeds).set_index(ftdf.index)
    Xres = img_space[img_space.index == num_item]
    Yres = img_space[img_space.index != num_item]
    img_matrix = pd.DataFrame(cosine_similarity(Xres,Yres)).T
    img_matrix.set_index(Yres.index, inplace=True)
    img_matrix.rename(columns={0:'resnet_similarity'}, inplace=True)
    img_matrix['resnet_similarity'].sort_values(ascending=False)

    cimg_space = pd.DataFrame(fcustom_embeds).set_index(ftdf.index)
    Xcustom = img_space[cimg_space.index == num_item]
    Ycustom = img_space[cimg_space.index != num_item]
    c_matrix = pd.DataFrame(cosine_similarity(Xcustom,Ycustom)).T
    c_matrix.set_index(Ycustom.index, inplace=True)
    c_matrix.rename(columns={0:'custom_similarity'}, inplace=True)
    c_matrix['custom_similarity'].sort_values(ascending=False)

    scaler = MinMaxScaler()

    recos = c_matrix.copy()
    recos['Custom'] = scaler.fit_transform(recos[['custom_similarity']])
    recos['Resnet'] = img_matrix['resnet_similarity']
    recos['Resnet'] = scaler.fit_transform(recos[['Resnet']])

    recos['Visual'] = (0.7 * recos.Resnet + 0.3*recos.Custom)

    recs = list(recos['Visual'].sort_values(ascending=False).index)
    return recs

def oppositerecs(likes, fresnet_embeds, fcustom_embeds, ftdf):
    #Similar to the above function, but returns the least similar items

    #Resnet
    rimg_space = pd.DataFrame(fresnet_embeds).set_index(ftdf.index)
    Xres = rimg_space.loc[likes]
    Yres = rimg_space.drop(likes)
    img_matrix = pd.DataFrame(cosine_similarity(Xres,Yres)).T
    img_matrix.set_index(Yres.index, inplace=True)
    img_matrix['Resnet'] = img_matrix.mean(axis=1)

    #Custom
    cimg_space = pd.DataFrame(fcustom_embeds).set_index(ftdf.index)
    Xcustom = cimg_space.loc[likes]
    Ycustom = cimg_space.drop(likes)
    c_matrix = pd.DataFrame(cosine_similarity(Xcustom,Ycustom)).T
    c_matrix.set_index(Ycustom.index, inplace=True)
    c_matrix['Custom'] = c_matrix.mean(axis=1)

    #Recs
    scaler = MinMaxScaler()
    recos = c_matrix.copy()
    recos = recos.rename(columns={'image_similarity':'Custom'})
    recos['Custom'] = scaler.fit_transform(recos[['Custom']])
    recos['Resnet'] = img_matrix['Resnet']
    recos['Resnet'] = scaler.fit_transform(recos[['Resnet']])

    recos['Visual'] = (0.7 * recos.Resnet + 0.3*recos.Custom)
    opporecs = list(recos.sort_values("Visual", ascending=True).index)
    return opporecs

def bestindex(fpado, fhisto, fstorage, fcounter, ratio, fresnet_embeds, fcustom_embeds, ftdf, non_tunnel_items_list, possible_items):
    #pado = df where each column = recommendations for a given item
    #memo = source of the last recommendation, ie index of last recommendation in pado
    #histo = dictionnary storing the indexes of the last recommendation for each soource / col in prado
    #the value of len(storage) and of sum(histo.values) are different because skipped items are stored into histo
    #In pado, the column 'divers' stores the type of the last 'out of the box' recommendation (0 if random)

    #introducing opposite / random suggestions
    if ((fcounter % ratio) == 0) and (fcounter != 0):
        #Once every x time, a different recommendation is made to test the appetite of the user for items
        #whose style is different from past liked items
        if (len(fstorage) % 2) == 0:
            #Half of the time, the recommendation is the opposite of past likes
            print('opposite')
            opposite_counter = 0
            likes = list(fpado.columns)[-5:]
            opposite_recommendations = oppositerecs(likes, fresnet_embeds, fcustom_embeds, ftdf)
            reco = opposite_recommendations[opposite_counter]
            if (reco in fstorage) or (reco not in non_tunnel_items_list):
                while (reco in fstorage) or (reco not in non_tunnel_items_list):
                    opposite_counter += 1
                    reco = opposite_recommendations[opposite_counter]
        else:
            #The other half of the time, the recommendation is generated randomly
            #Ranomly output the index of a non-tunnel item (not black pant, white shirt, black sweat...)
            print('random')
            reco = random.randint(0, (len(non_tunnel_items_list) - 1))
            if reco in fstorage:
                while reco in fstorage:
                    reco = random.randint(0, (len(non_tunnel_items_list) - 1))

    # regular suggestions
    else:
        memo = min(fhisto, key=fhisto.get)
        print(f"Index of the clothe from which the next recommendation is derived from: {memo}")
        print(f"Histo: {fhisto}")
        reco = fpado[memo][fhisto[memo]]

        if reco in fstorage:
            while reco in fstorage:
                reco = fpado[memo][fhisto[memo] + 1]
                fhisto[memo] = (fhisto[memo] + 1)

        if reco not in possible_items:
            while reco not in possible_items:
                reco = fpado[memo][fhisto[memo] + 1]
                fhisto[memo] = (fhisto[memo] + 1)

        fhisto[memo] = (fhisto[memo] + 1)
    fstorage.append(reco)
    return (reco, fhisto, fstorage)

def is_tunnel(pado, histo, tunnel_rate):
    #from the number of columns (ie accepted recommendations) and the number of rows (ie of total recommendations)
    #Determine if in a 'tunnel', ie a situation where recommendations are stuck outside of center of interest of user
    #Use histo and not storage to only take into account recommendations made by the algo and not the out of the box
    #tunnel_rate : shape of the tunnel, ie distance between good recs and total recs
    row = max(histo.values())
    col = len(pado.columns)
    if ((tunnel_rate * col) > row) == False:
        #In a tunnel -> algo suggest wrong recommendations and will continue to do so
        #Need to increase the rate of 'out of the box' suggestions to find an aesthetic liked by user
        ratio = 5
    else:
        #Not in a tunnel -> return ratio
        ratio = 7
    return ratio

def non_tunnel_items(resnet_embeds, eps_rate):
    #Returns a list of items that are not too similar from one another
    #ie excludes all the white shirts, blue jeans... that are visually nearly identical
    #Based only on resnet embedings
    matrix = cosine_similarity(resnet_embeds)
    #Non supervised ML algo to find the number of clusters
    clustering = DBSCAN(eps=eps_rate).fit(matrix)
    labels = clustering.labels_
    #Rank the clusters by their population
    #The first & largest cluster is all the items not grouped because of their high similarity (ie black pants...)
    value_counts = pd.DataFrame(labels).value_counts()
    non_tunnel_labels = value_counts.index[0]
    non_tunnel_items_list = list(np.where(labels == non_tunnel_labels)[0])
    return non_tunnel_items_list

def contains_strings(list_sizes):
    #Function that allows to transform a list of filter options into a string
    #In the X|Y format which can be passed as an argument to .str.contains
    contain = list_sizes[0]
    if len(list_sizes) > 1:
        for i in list_sizes[1:]:
            contain = contain + "|" + i
    return contain

#-------------------
#-------GCP---------
#-------------------

def get_gcp_user_data(userID):
    #Load user data
    #https://stackoverflow.com/questions/60729667/reading-and-writing-pickles-using-google-cloud
    #https://pypi.org/project/google-cloud-storage/
    client = storage.Client()
    bucket = client.get_bucket('...')
    path = "'Data/Data/Users/" + str(userID) + "/" + str(userID)

    pado_path = path[1:] + "_pado.pickle"
    pado_blob = bucket.blob(pado_path)
    pado_pickle = pado_blob.download_as_string()
    pado = pickle.loads(pado_pickle)

    histo_path = path[1:] + "_histo.pickle"
    histo_blob = bucket.blob(histo_path)
    histo_pickle = histo_blob.download_as_string()
    histo = pickle.loads(histo_pickle)

    storage_path = path[1:] + "_storage.pickle"
    storage_blob = bucket.blob(storage_path)
    storage_pickle = storage_blob.download_as_string()
    dst = pickle.loads(storage_pickle)
    stg = list(dst[0])

    ratio_path = path[1:] + "_ratio.pickle"
    ratio_blob = bucket.blob(ratio_path)
    ratio_pickle = ratio_blob.download_as_string()
    ratio_dic = pickle.loads(ratio_pickle)
    oob_ratio = ratio_dic['oob_ratio']

    del pado_blob, pado_pickle, histo_blob, histo_pickle, storage_blob, storage_pickle, ratio_blob, ratio_pickle

    return pado, histo, stg, oob_ratio

def get_gcp_df_data(gender):
    #Load items data (ie titles, brands etc...) and their embeddings
    client = storage.Client()
    bucket = client.get_bucket('...')

    if gender == "M": #Masculine clothes
        path = "Data/Data/Men/"
    if gender == "W":
        path = "Data/Data/Women/"

    tdf = pd.read_csv("gs://.../" + path + "Raw/EndYoox_" + gender + "_Sorting.csv")
    #https://stackoverflow.com/questions/56990590/can-i-download-from-google-storage-blobs-into-a-vm-as-an-n-d-array
    resnet_blob = bucket.blob(path + "Embeddings/Embeddings_" + gender + "_resnet.npy")
    with io.BytesIO() as in_memory_resnet_file:
        resnet_blob.download_to_file(in_memory_resnet_file)
        in_memory_resnet_file.seek(0)
        resnet_embeddings = np.load(in_memory_resnet_file)

    custom_blob = bucket.blob(path + "Embeddings/Embeddings_" + gender + "_custom.npy")
    with io.BytesIO() as in_memory_custom_file:
        custom_blob.download_to_file(in_memory_custom_file)
        in_memory_custom_file.seek(0)
        custom_embeddings = np.load(in_memory_custom_file)

    print(f"tdf shape: {tdf.shape} | resnet shape: {resnet_embeddings.shape} | custom shape: {custom_embeddings.shape}")
    del resnet_blob, custom_blob
    return tdf, resnet_embeddings, custom_embeddings

def save_gcp_user_data(userID, pado, histo, stg, oob_ratio):
    #Save the modified user data
    client = storage.Client()
    bucket = client.get_bucket('...')
    path = "'Data/Data/Users/" + str(userID) + "/" + str(userID)

    pado_blob = bucket.blob(path[1:] + "_pado.pickle")
    pado_pickle = pickle.dumps(pado)
    pado_blob.upload_from_string(pado_pickle)

    histo_blob = bucket.blob(path[1:] + "_histo.pickle")
    histo_pickle = pickle.dumps(histo)
    histo_blob.upload_from_string(histo_pickle)

    storage_blob = bucket.blob(path[1:] + "_storage.pickle")
    dst = pd.DataFrame(stg)
    storage_pickle = pickle.dumps(dst)
    storage_blob.upload_from_string(storage_pickle)

    ratio_blob = bucket.blob(path[1:] + "_ratio.pickle")
    ratio_dic = {'oob_ratio':int(oob_ratio)}
    ratio_pickle = pickle.dumps(ratio_dic)
    ratio_blob.upload_from_string(ratio_pickle)

    del pado_blob, pado_pickle, histo_blob, histo_pickle, storage_blob, storage_pickle, ratio_blob, ratio_pickle

    return "recommendation_data_saved"
