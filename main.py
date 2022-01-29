import requests
from datetime import datetime as dt
from pprint import PrettyPrinter

import tweepy
from dotenv import dotenv_values


print = PrettyPrinter(indent=4).pprint

config = dotenv_values(".env")

NASA_API_KEY = config.get("NASA_API_KEY")
TWITTER_API_KEY = config.get("TWITTER_API_KEY")
TWITTER_API_KEY_SECRET = config.get("TWITTER_API_KEY_SECRET")
TWITTER_ACCESS_TOKEN = config.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = config.get("TWITTER_ACCESS_TOKEN_SECRET")

APOD = "Astronomy Picture of the Day"
apod_url = "https://api.nasa.gov/planetary/apod"

# Tweepy authentication
auth=tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_KEY_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
twitter_api=tweepy.API(auth)
# NOTE: consumer_key == api_key
# NOTE: consumer_secret == api_key_secret


def main():
    # NOTE: downloading pic from NASA
    payload = {}
    count = 0
    while "hdurl" not in payload:
        payload = requests.get(f"{apod_url}?api_key={NASA_API_KEY}").json()
        count += 1
        if count >= 5:
            break

    image_url = payload.get("hdurl", None)
    image = requests.get(f"{image_url}?api_key={NASA_API_KEY}")
    file_extension = image_url[image_url.rfind("."):]

    # NOTE: saving pic in a file. Could be skipped
    if image:
        title = payload.get("title", str(dt.now()))
        path = f"images/{title}{file_extension}"
        with open(path, "wb") as f:
            f.write(image.content)

        # NOTE: uploading pic to Twitter
        response = twitter_api.media_upload(path)
        media_id = response.media_id
        copyright = payload.get("copyright", None)
        message = title
        message += f"\nSource: NASA ({APOD})\n"
        tags = "\n#nasa #apod #photo"
        if copyright:
            message += f"Copyright: {copyright}"

        message += tags

        twitter_api.update_status(status=message, media_ids=[media_id])


if __name__ == "__main__":
    main()