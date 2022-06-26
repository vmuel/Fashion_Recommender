# Content-based fashion recommender system

Recommender system based on the cosine similarity between the embeddings of images of clothes extracted from a ResNet-50 and a custom CNN model trained to classify the style of clothes.
Url: https://fashion-recommender-cnn.herokuapp.com/ (if available)

## Source of the data

The data was scrapped from various websites and comprises of:
* A pandas DataFrame with information on each items such as the brand, the title of the item, its price, description...
* A numpy array with cut-ouf color images of every clothes (size: (x, 224, 224, 224)).

## Deep Learning
Two models were trained to identify the style of an item (rather than the color or category) in order to capture in the FC layer a representation of an aesthetic more than a representation of physical attributes.
I used the embeddings extracted from a ResNet-5O model (70% of the weight of recommendations) and a custom CNN model (30%).

The models were designed and trained in Jupyter Notebook, and the notebooks for the 4 models (ResNet and Custom for womenswear & menswear each) can be found in /deep_learning_notebooks.
An additional notebook, used to extract the embeddings and to prepare the data to make possible sorting by budget, size & category (thanks to a computer vision classifying algorithm) can also be found in this folder -even though this latter functionality is not acessible in the web app.

## Algorithm
The algorithm makes recommendation based on the items liked by the user.
More specifically, for each item liked, the algorithm returns a list of recommendations ranked by how similar their style is to the item liked.

To do so, the algorithm measures the cosine similarity of the embeddings of the images of clothes extracted from the ResNet-50 and custom CNN models.

To avoid being 'stuck' only recommending items too similar to one another (such as white shirts or blue jeans), the algorithm uses clustering to exclude such items and makes from time to time random / different recommendations.

## Deployment
The deployment of the app was built around two API endpoints:
- '/register' : used to initiate a user profile
- '/recommend' : given a list of item liked, returns a recommendation (the aforementioned algorithm)

The items data (i.e. the pandas DataFrame and the ResNet-50 & custom model embeddings) and the user data are stored in Google Cloud Storage and accessed during each API requests to generate recommendations. I used blops and pickle files to load the data from Cloud Storage.

The API was built in a Docker image and hosted on Google Cloud Run.

The 'app' folder is the code for the webapp, designed with streamlit and hosted on Heroku (free dynos plan).
