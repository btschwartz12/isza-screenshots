from datetime import datetime, timedelta
import json
import os
from flask import request
from instagrapi import Client
from shared import app


def post_image(username, password, paths, caption, maxtries, test=True):
    if test:
        print("Test mode: not posting to Instagram")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Paths: {paths}")
        print(f"Caption: {caption}")
        return {'message': 'Image posted successfully'}
    cl = Client()

    if len(paths) == 0:
        print("No paths provided")
        return None
    
    attempts = 0

    while attempts < maxtries:
        try:
            cl.login(username, password)
            if len(paths) == 1:
                media = cl.photo_upload(path=paths[0], caption=caption)
            else:
                media = cl.album_upload(paths, caption=caption)
            cl.logout()
            return media
        except Exception as e:
            attempts += 1
            print("Error: ", e)
    
    return None



