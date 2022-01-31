import random
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

nasa_base_url = "https://api.nasa.gov"
ROVER_CAMERAS = ["FHAZ", "RHAZ", "MARDI", "NAVCAM", "PANCAM"]
APOD = "Astronomy Picture of the Day"
apod_url = f"{nasa_base_url}/planetary/apod"
rovers_photos_url = f"{nasa_base_url}/mars-photos/api/v1/rovers/curiosity/photos"


# Tweepy authentication
auth=tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_KEY_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
twitter_api=tweepy.API(auth)
# NOTE: consumer_key == api_key
# NOTE: consumer_secret == api_key_secret



def main(api, cam):
    # NOTE: downloading pic from NASA
    payload = {}
    count = 0
    error = False
    sol = random.randrange(1000)

    if api == 0:
        while "hdurl" not in payload:
            try:
                payload = requests.get(f"{apod_url}?api_key={NASA_API_KEY}").json()
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
    else:
        cam = ROVER_CAMERAS[cam]
        payload = requests.get(f"{rovers_photos_url}?api_key={NASA_API_KEY}&camera={cam}&sol={sol}").json()
        rover_name = None # photos[0].rover.name
        camera_name = None # photos[0].camera.full_name
        img_src = None # photos[0].img_src
        image = None
        date = None
        # sol = arriba
        if payload and payload.get("photos", []):
            for item in payload.get("photos", {}):
                rover_name = item.get("rover", {}).get("name", "")
                camera_name = item.get("camera", {}).get("full_name", "")
                img_src = item.get("img_src", None)
                date = item.get("earth_date", "")
                break

            try:
                img_src = img_src.replace("http://mars.jpl.nasa.gov/", "https://mars.nasa.gov/")
                image = requests.get(img_src)
            except Exception as e:
                error = True
                print(f"Error: {e}")

        if not error and image:
            file_extension = img_src[img_src.rfind("."):]
            path = f"images/{rover_name}-{camera_name}-{date}-sol_{sol}{file_extension}"
            with open(path, "wb") as f:
                f.write(image.content)

            # NOTE: uploading pic to Twitter
            response = twitter_api.media_upload(path)
            media_id = response.media_id
            copyright = payload.get("copyright", None)
            message = camera_name
            message += f"\nSource: NASA - ROVER ({rover_name})\n"
            message += f"Date: {date} - Sol: {sol}\n"
            tags = "\n#nasa #apod #photo #rover"
            if copyright:
                message += f"Copyright: {copyright}"

            message += tags

            twitter_api.update_status(status=message, media_ids=[media_id])


if __name__ == "__main__":
    api_type = random.randrange(2)
    cam_type = random.randrange(5)
    main(api_type, cam_type)