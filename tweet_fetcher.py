#!/usr/bin/python
import tweepy
import json
import requests
import os
import torch
import torchvision
import sys
import pickle
from fastai.vision.all import * 

from PIL import Image

consumer_key = os.getenv("CONSUMER_API_KEY")
consumer_secret_key = os.getenv("CONSUMER_API_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

auth = tweepy.OAuthHandler(consumer_key, consumer_secret_key)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# Load the PyTorch model
# model = torch.load('model.pth')
# model.eval()

# Load the model from the .pkl file
learn = load_learner('./midwit_model.pkl')

def prediction():
    # Use the model to predict on an image
    label, _, probs = learn.predict("./image.jpg")
    print(label)
    return label == 'midwitmeme'

# Respond to a tweet that mentions the bot
def respondToTweet(file='tweet_ID.txt'):
    # Get the last tweet ID that the bot replied to
    response = requests.get(os.getenv("BACKEND_URL") + "/last-seen")
    last_id_json = response.json()
    if len(last_id_json["rows"]) == 0:
        last_id = 0
    else:
        last_id = last_id_json["rows"][0]["tweetTagId"]
    print(last_id)

    # Get the mentions
    mentions = api.mentions_timeline(count=int(last_id), tweet_mode='extended')
    if len(mentions) == 0:
        return

    new_id = 0
    print("someone mentioned me...")

    for mention in reversed(mentions):

        if (int(mention.id) <= int(last_id)):
            print("same id, continuing...")
            continue
        print(str(mention.id) + '-' + mention.full_text)

        tweet_status = api.get_status(id=mention.id, tweet_mode='extended')
        original_tweet_id = mention.id
        # Check if the tweet is a reply and update status to the top tweet
        if tweet_status.in_reply_to_status_id:
            # Fetch the top tweet if the tweet is a reply
            original_tweet_id = tweet_status.in_reply_to_status_id
            tweet_status = api.get_status(original_tweet_id, tweet_mode='extended')

        response = requests.get(os.getenv("BACKEND_URL") + "/tweet-exists/" + str(original_tweet_id))
        print(response)
        print("THIS IS THE RESPONSE")
        print(response.json())
        tweet_exists = response.json()
        if (tweet_exists):
            print("Tweet already exists in database")
            continue

        # Extract the image from the tweet
        print("Extracting image from tweet")
        if "media" in tweet_status.entities:
            media = tweet_status.entities["media"][0]
            media_url = media["media_url_https"]
            print("Image url: " + media_url + "")
        else:
            print("No media found in tweet")
            continue

        # Download the image
        print("Downloading image from " + media_url + "")
        image_data = requests.get(media_url).content
        with open('image.jpg', 'wb') as f:
            f.write(image_data)

        # Check if the image is a certain meme type
        if prediction():
            # Add the link to the tweet containing the image to the database
            tweet_url = f"https://twitter.com/{tweet_status.user.screen_name}/status/{tweet_status.id_str}"
            requests.post(os.getenv('BACKEND_URL') + '/add-tweet', json={
                'tweetId': tweet_status.id_str,
                'tweetUrl': tweet_url,
                'tweetImageUrl': media_url,
                'tweetAuthor': tweet_status.user.screen_name,
                'tweetTagAuthor': mention.user.screen_name,
                'tweetTagId': mention.id_str
            })

            print("liking and replying to tweet")
            # Reply to the tagged tweet with the message "Success"
            api.create_favorite(mention.id)
            status = "This meme has been added to www.midwitmeme.com!"
            in_reply_to_status_id = mention.id
            api.update_status(status=status, in_reply_to_status_id=in_reply_to_status_id, auto_populate_reply_metadata=True)

if __name__=="__main__":
    respondToTweet()