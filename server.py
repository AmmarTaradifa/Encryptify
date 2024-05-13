import os
import pathlib
import enkripsi, dekripsi, googleDriveAPI

import requests
import flask
import json
import tempfile

from flask import Flask,render_template, session, abort, redirect, request, send_file, jsonify
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
from googleapiclient.discovery import build
from werkzeug.utils import secure_filename


app = Flask("Google Login App")
app.secret_key = "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" # make sure this matches with that's in client_secret.json

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1" # to allow Http traffic for local dev

GOOGLE_CLIENT_ID = "554395474590-nmgu5h95bhmi7tofot8mqo7mljjicdqk.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
ACCESS_TOKEN_URI = 'https://www.googleapis.com/oauth2/v4/token'

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid", "https://www.googleapis.com/auth/drive.file"],
    redirect_uri="https://encryptify-five.vercel.app/callback"
)


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper

def build_credentials():
    # Get the OAuth 2.0 tokens from the session
    oauth2_tokens = flask.session.get("credentials")

    # Check if the tokens exist in the session
    if not oauth2_tokens:
        raise Exception("OAuth 2.0 tokens not found in session")

    # Parse the tokens into a dictionary
    oauth2_tokens_dict = json.loads(oauth2_tokens)

    # Extract the necessary token values
    access_token = oauth2_tokens_dict.get("token")
    refresh_token = oauth2_tokens_dict.get("refresh_token")

    # Build and return the credentials object
    return google.oauth2.credentials.Credentials(
        token=access_token,
        refresh_token=refresh_token,
        client_id=GOOGLE_CLIENT_ID,
        client_secret="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",
    )
 

@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")

    credentials_obj = Credentials(
        token=credentials.token,
        refresh_token=credentials.refresh_token,
        id_token=credentials.id_token,
        token_uri=credentials.token_uri,
        client_id=credentials.client_id,
        client_secret=credentials.client_secret
    )
    people_api_service = build('people', 'v1', credentials=credentials_obj)
    person_info = people_api_service.people().get(resourceName='people/me', personFields='photos').execute()

    # Ekstrak URL foto profil dari respons API
    photo_url = person_info.get('photos', [])[0].get('url')

    # Simpan URL foto profil di session atau kirim langsung ke template
    session["photo_url"] = photo_url
    session["credentials"] = credentials.to_json()

    #  # Panggil fungsi uploadFiles dengan menyediakan session_state
    # googleDriveAPI.uploadFiles(['file_path_1', 'file_path_2'], )
    
    return redirect("/main")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/")
def index():
    # return "Hello World <a href='/login'><button>Login</button></a>"
    return render_template('login.html')



@app.route("/main")
@login_is_required
def protected_area():
    return render_template('index.html')
    # 
    # return f"Hello {session['name']}! <br/> <a href='/logout'><button>Logout</button></a>"

@app.route('/encrypt', methods=['POST'])
def encrypt():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        
        try:
            # Simpan file sementara di direktori /tmp
            file_path = os.path.join(os.environ['TMPDIR'], filename)
            uploaded_file.save(file_path)
            
            # Generate encryption key
            key = enkripsi.generate_key(file_path)
            
            # Encrypt file
            enkripsi.encrypt_file(file_path, key)
            
            # Upload encrypted file to Google Drive
            encrypted_file_path = file_path + '.encrypted'
            key_path = file_path + '.key'
            file_paths = [encrypted_file_path, key_path]
            googleDriveAPI.uploadFile(file_paths)
            
            # Cleanup
            os.remove(encrypted_file_path)
            os.remove(key_path)
            os.rmdir(temp_dir)
            
            alert_message = f"File {filename} berhasil terenkripsi dan diunggah ke Google Drive!"
            return f'<script>alert("{alert_message}"); window.location.replace("/main");</script>'
        except Exception as e:
            error_message = f"Enkripsi dan unggah file gagal: {str(e)}"
            return f'<script>alert("{error_message}"); window.location.replace("/main");</script>'

        
@app.route('/decrypt', methods=['POST'])
def decrypt():
    if request.method == 'POST':
        try:
            # Mengambil file yang diunggah dari permintaan POST
            uploaded_file = request.files['file']
            
            # Menyimpan file yang diunggah ke dalam direktori Downloads
            download_directory = os.path.join(os.path.expanduser('~'), 'Downloads')
            file_path = os.path.join(download_directory, uploaded_file.filename)
            uploaded_file.save(file_path)
            
            # Mengambil file kunci yang diunggah dari permintaan POST
            key_file = request.files['key_path']
            
            # Menyimpan file kunci ke dalam direktori Downloads
            key_path = os.path.join(download_directory, key_file.filename)
            key_file.save(key_path)

            # Membaca kunci dari file
            with open(key_path, 'rb') as key_file:
                key = key_file.read()
                
            if key:
                # Melakukan dekripsi pada file
                dekripsi.decrypt_file(file_path, key)
                os.remove(file_path)
                os.remove(key_path)

            # Menyiapkan pesan alert
            alert_message = f"File {uploaded_file.filename} berhasil didekripsi!"
            alert_type = "success"  # Jenis alert berhasil

        except Exception as e:
            # Jika terjadi kesalahan, tangkap dan tampilkan pesan kesalahan
            alert_message = f"Terjadi kesalahan saat melakukan dekripsi: {str(e)}"
            alert_type = "error"  # Jenis alert kesalahan

        # Mengembalikan response dalam format JavaScript untuk menampilkan alert
        return f'<script>alert("{alert_message}"); window.location.replace("/main");</script>'



if __name__ == "__main__":
    app.run(host='localhost', debug=True)
