import requests
import json

def load_recommendation(userID, gender, feedback):
    api_url = 'https://tokfin-ux2qpjxuga-nn.a.run.app/'
    recommendation_params = {
        'userID': userID,
        'response': feedback,
        'sizes':'0X-Large_1X-Large_32"_33"',
        'categories':'shirts_pants_coats',
        'gender':gender,
        'budget':'3',
        'is_filter':'n'}
    recommendation_response = requests.get(api_url + "recommend", params=recommendation_params)
    reco = recommendation_response.json()
    iTitle = reco['Title']
    iBrand = reco['Brand']
    iDescription = reco['Description']
    iSize = reco['Size']
    iPrice = reco['Price']
    iSale = reco['Sale']
    iLink = reco['Product_link']
    #iCutoff = reco['Cutoff']
    #iImg2 = reco['Image2']
    #iImg3 = reco['Image3']
    iCutoff_img = reco['Cutoff_img']
    iCutoff_shape = reco['Cutoff_shape']

    return iTitle, iBrand, iDescription, iSize, iPrice, iSale, iLink, iCutoff_img, iCutoff_shape
