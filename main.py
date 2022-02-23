import random
import requests
import time
from datetime import datetime as dt
from pprint import PrettyPrinter

import tweepy
from dotenv import dotenv_values


print = PrettyPrinter(indent=4).pprint
config = dotenv_values(".env")

NASA_API_KEY = config.get("NASA_API_KEY")
TWITTER_API_KEY = config.get("TWITTER_API_KEY") # consumer_key == api_key
TWITTER_API_KEY_SECRET = config.get("TWITTER_API_KEY_SECRET") # consumer_secret == api_key_secret
TWITTER_ACCESS_TOKEN = config.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = config.get("TWITTER_ACCESS_TOKEN_SECRET")
ROVER_CAMERAS = ["FHAZ", "RHAZ", "MARDI", "NAVCAM", "PANCAM"]
APOD = "Astronomy Picture of the Day"

ROVER_SOL_LIMIT = 3362 # 05/02/2022
NASA_BASE_URL = "https://api.nasa.gov"
NASA_APOD_URL = f"{NASA_BASE_URL}/planetary/apod"
ROVERS_PHOTOS_URL = f"{NASA_BASE_URL}/mars-photos/api/v1/rovers/curiosity/photos"

# Tweepy authentication
auth=tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_KEY_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
twitter_api=tweepy.API(auth)


def get_apod_image():
    payload = {}
    count = 0
    error = False

    while "hdurl" not in payload:
        try:
            payload = requests.get(f"{NASA_APOD_URL}?api_key={NASA_API_KEY}").json()
        except Exception as e:
            error = True
            print(f"Error: {e}")

        count += 1
        if count >= 3:
            break

    image_url = payload.get("hdurl", None)

    try:
        image = requests.get(f"{image_url}?api_key={NASA_API_KEY}")
    except Exception as e:
        error = True
        print(f"Error 2: {e}")

    if not error:
        file_extension = image_url[image_url.rfind("."):]

        # NOTE: saving pic in a file
        if image:
            title = payload.get("title", str(dt.now()))
            path = f"images/{title}{file_extension}"
            with open(path, "wb") as f:
                f.write(image.content)

            return path, payload


def get_rover_image():
    sol = random.randrange(ROVER_SOL_LIMIT)
    cam = ROVER_CAMERAS[random.randrange(len(ROVER_CAMERAS))]
    payload = requests.get(f"{ROVERS_PHOTOS_URL}?api_key={NASA_API_KEY}&camera={cam}&sol={sol}").json()
    image = None
    error = False

    if payload and payload.get("photos", {}):
        for item in payload.get("photos", {}):
            rover_name = item.get("rover", {}).get("name", "")
            camera_name = item.get("camera", {}).get("full_name", "")
            img_src = item.get("img_src", None)
            date = item.get("earth_date", "")
            break

        try:
            img_src = img_src.replace("jpl.", "")
            img_src = img_src.replace("http", "https")
            image = requests.get(img_src)
        except Exception as e:
            error = True
            print(f"Error: {e}")

    if not error and image:
        file_extension = img_src[img_src.rfind("."):]
        path = f"images/{rover_name}-{camera_name}-{date}-sol_{sol}{file_extension}"
        with open(path, "wb") as f:
            f.write(image.content)

        return path, payload


def post_image_to_twitter(path, payload, apod=False):
    tags = payload.get("tags")
    response = twitter_api.media_upload(path)
    media_id = response.media_id
    copyright = payload.get("copyright", None)

    if apod:
        message = payload.get("title", str(dt.now()))
        message += f"\nSource: NASA ({APOD})\n"
    else:
        photos = payload.get("photos", [])
        if photos:
            message = photos[0].get("camera", {}).get("full_name", "")
            rover_name = photos[0].get("rover", {}).get("name", "")
            message += f"\nSource: NASA - ROVER ({rover_name})\n"
            date = photos[0].get("earth_date", "")
            message += f"Date: {date}\n"

    if copyright:
        message += f"Copyright: {copyright}\n"

    message += " ".join(tags)

    twitter_api.update_status(status=message, media_ids=[media_id])


def main():
    path, payload = get_apod_image()
    payload.update(tags=["#nasa", "#apod"])
    post_image_to_twitter(path, payload, apod=True)

    time.sleep(300) # wait 5 minutes between images

    path, payload = get_rover_image()
    payload.update(tags=["#rover", "#curiosity", "#nasa", "#esa"])
    post_image_to_twitter(path, payload)


if __name__ == "__main__":
    main()