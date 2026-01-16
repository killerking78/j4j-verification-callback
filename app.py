from flask import Flask, request
import requests, json, os

app = Flask(__name__)

# Load these from Railway environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

USERS_FILE = "users.txt"  # txt is better for structured data

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    user_id = request.args.get("state")  # Discord allows state param for identifying user

    if not code or not user_id:
        return "Missing code or user ID", 400

    # Exchange code for token
    r = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
           
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if r.status_code != 200:
        return f"Authorization failed: {r.text}", 400

    token = r.json().get("access_token")
    if not token:
        return "Failed to get access token", 400

    # Save token per user
    users = load_users()
    users[user_id] = token
    save_users(users)

    return "Authorization successful! You can return to Discord."

@app.route("/")
def home():
    return "Callback server running."

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
