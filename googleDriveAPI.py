from __future__ import print_function
import os
import io
import zipfile
import time
import flask
from flask import Flask,render_template, session, abort, redirect, request, send_file, jsonify


import googleapiclient.discovery
from server import build_credentials
from apiclient import discovery
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Fungsi-fungsi untuk berinteraksi dengan Google Drive


app = flask.Blueprint('google_drive', __name__)

def build_drive_api_v3():
    credentials = build_credentials()
    return googleapiclient.discovery.build('drive', 'v3', credentials=credentials).files()

def check_folder_exists(drive_api, folder_name):
    # Cek apakah folder dengan nama yang diberikan sudah ada di Google Drive
    response = drive_api.list(q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                                      spaces='drive', fields='files(id)').execute()
    folders = response.get('files', [])
    return folders

def uploadFile(file_paths):

    drive_api = build_drive_api_v3()

   # Cek apakah folder "Encripyfy Files" sudah ada
    folder_name = 'Encripyfy Files'
    existing_folders = check_folder_exists(drive_api, folder_name)

    if existing_folders:
        folder_id = existing_folders[0]['id']
    else:
        # Jika tidak ada, buat folder baru
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = drive_api.create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')

    base_file_name = os.path.basename(file_paths[0])
    # Buat nama file zip dari timestamp saat ini
    zip_file_name = f"{base_file_name}_files_{time.time()}.zip"

    zip_directory = os.path.join(os.path.expanduser('~'), 'Downloads/Encryptify')
    if not os.path.exists(zip_directory):
        os.makedirs(zip_directory)
    
    zip_file_path = os.path.join(zip_directory, zip_file_name)

    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in file_paths:
            zipf.write(file_path, os.path.basename(file_path))
        zipf.close()

        file_metadata = {
            'name': zip_file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(zip_file_path, mimetype='application/zip')
        drive_api.create(body=file_metadata, media_body=media, fields='id').execute()
        # os.remove(zip_file_name)
