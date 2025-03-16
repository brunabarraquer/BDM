import requests
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Set your Letterboxd API credentials
API_KEY = os.getenv('LBXD_API_KEY')
API_SECRET = os.getenv('LBXD_API_SECRET')
USERNAME = os.getenv('LBXD_USERNAME')
PASSWORD = os.getenv('LBXD_PASSWORD')

# Function to obtain an access token
def get_access_token():
    url = 'https://api.letterboxd.com/api/v0/auth/token'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    data = {
        'grant_type': 'password',
        'username': USERNAME,
        'password': PASSWORD,
    }
    response = requests.post(url, headers=headers, json=data, auth=(API_KEY, API_SECRET))
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        raise Exception(f'Error obtaining access token: {response.status_code} {response.text}')

# Function to retrieve comments for a specific list
def get_list_comments(list_id, access_token):
    url = f'https://api.letterboxd.com/api/v0/list/{list_id}/comments'
