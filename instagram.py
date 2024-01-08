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



# @app.route('/api/v1/insta/post', methods=['POST'])
# def post_insta():

#     file = request.files.get('image')
#     caption = request.form.get('caption')
#     if not file:
#         return {'error': "No 'image' provided"}, 400
#     if not caption:
#         return {'error': "No 'caption' provided"}, 400
    
#     username = os.getenv('INSTAGRAM_USERNAME')
#     password = os.getenv('INSTAGRAM_PASSWORD')

#     path = f'/tmp/{file.filename}'
#     file.save(path)

#     media = post_image(username, password, path, caption, os.getenv('MAX_TRIES'))

#     if not media:
#         return {'error': "Failed to post image"}, 500
    
#     os.remove(path)
    
#     return {'message': 'Image posted successfully'}, 200




