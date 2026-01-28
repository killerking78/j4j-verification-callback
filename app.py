# app.py
from flask import Flask, request, redirect, jsonify
import requests, os, json

app = Flask(__name__)

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GUILD_ID = os.getenv("GUILD_ID")  # server to auto-join users
BOT_TOKEN = os.getenv("BOT_TOKEN")  # bot token for adding users

USERS_FILE = "users.json"

# Load/save authorized users
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/")
def home():
    return "OAuth callback server is running!"

@app.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")  # optional user ID

    if not code:
        return "Missing authorization code.", 400

    # Exchange code for access token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": "identify guilds.join guilds"
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    token_resp = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    token_json = token_resp.json()
    access_token = token_json.get("access_token")
    if not access_token:
        return f"Authorization failed: {token_json}", 400

    # Get user info
    user_resp = requests.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {access_token}"})
    user = user_resp.json()

    # Add user to your server (requires bot token)
    add_resp = requests.put(
        f"https://discord.com/api/guilds/{GUILD_ID}/members/{user['id']}",
        headers={
            "Authorization": f"Bot {BOT_TOKEN}",
            "Content-Type": "application/json"
        },
        json={"access_token": access_token}
    )

    # Save token
    users = load_users()
    users[user['id']] = token_json
    save_users(users)

    return f"Authorization successful! Welcome, {user.get('username', 'user')}."

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
