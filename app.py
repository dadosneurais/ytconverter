from flask import Flask, render_template, request, send_file
from yt_dlp import YoutubeDL
import os
from datetime import datetime as dt
from dotenv import load_dotenv
import requests
from pymongo import MongoClient

app = Flask(__name__)

DOWNLOAD_DIR = os.path.abspath('')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

### INÍCIO DO ESQUELETO PRINCIPAL IP ###
def get_client_ip():
    if 'X-Forwarded-For' in request.headers:
        ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
    else:
        ip = request.remote_addr
    return ip

# Função para obter a localização a partir do IP
def get_location(ip):
    url = f'http://ipinfo.io/{ip}/json'
    data = requests.get(url).json()
    return data.get('loc', '0,0')
# Carregar variáveis do .env
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Conectar ao MongoDB
client = MongoClient(MONGO_URI)
db = client['db_youtube']
logs_collection = db['logs']

# Função para salvar logs no MongoDB
def save_log_to_db(ip):
    timestamp = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    location = get_location(ip)

    log_data = {
        "ip": ip,
        "location": location,
        "timestamp": timestamp
    }
    logs_collection.insert_one(log_data)
    ### FIM DO ESQUELETO PRINCIPAL ###


@app.route('/', methods=['GET', 'POST'])
def index():
    
    # INÍCIO SALVANDO ACESSO IP
    ip = get_client_ip()
    if request.method == 'GET':
        save_log_to_db(ip)  
    # FIM ACESSO IP


    if request.method == 'POST':
        video_url = request.form.get('url')
        download_format = request.form.get('format')  # 'mp3' ou 'mp4'

        if not video_url or download_format not in ['mp3', 'mp4']:
            return render_template('index.html', error="URL ou formato inválido")

        if download_format == 'mp3':
            outtmpl = os.path.join(DOWNLOAD_DIR, '%(title)s.mp3')
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': outtmpl,
            }
        else:  # mp4
            outtmpl = os.path.join(DOWNLOAD_DIR, '%(title)s.mp4')
            ydl_opts = {
                'merge_output_format': 'mp4',
                'outtmpl': outtmpl,
            }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            if download_format == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
            else:
                filename = os.path.splitext(filename)[0] + '.mp4'

        return send_file(filename, as_attachment=True)

    return render_template('index.html', ip=ip)


if __name__ == '__main__':
    app.run(debug=True)
