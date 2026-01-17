# callback_server.py
from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# Environment variables - set these in Railway
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# File to store tokens
TOKENS_FILE = "user_tokens.json"

def load_tokens():
    """Load existing tokens from file"""
    if not os.path.exists(TOKENS_FILE):
        return {}
    try:
        with open(TOKENS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_tokens(tokens):
    """Save tokens to file"""
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

@app.route("/")
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "running",
        "message": "Discord OAuth callback server is active"
    })

@app.route("/callback")
def callback():
    """Handle OAuth callback from Discord"""
    
    # Get code and state from Discord's redirect
    code = request.args.get("code")
    user_id = request.args.get("state")
    
    # Validate we have both parameters
    if not code:
        return "Error: No authorization code received", 400
    
    if not user_id:
        return "Error: No user ID received", 400
    
    # Validate environment variables are set
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        return "Error: Server configuration missing", 500
    
    # Exchange authorization code for access token
    try:
        token_response = requests.post(
            "https://discord.com/api/v10/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        # Check if token exchange was successful
        if token_response.status_code != 200:
            error_data = token_response.json()
            return f"Error: {error_data.get('error_description', 'Token exchange failed')}", 400
        
        # Extract access token
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            return "Error: No access token in response", 400
        
        # Save token for this user
        tokens = load_tokens()
        tokens[user_id] = access_token
        save_tokens(tokens)
        
        # Success response
        return """
        <html>
        <head>
            <title>Authorization Successful</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: #5865F2;
                }
                .container {
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                h1 { color: #5865F2; margin-bottom: 10px; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✅ Authorization Successful!</h1>
                <p>You can now close this window and return to Discord.</p>
                <p>Use the <code>/join</code> command to start earning tokens!</p>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route("/api/get_token/<user_id>")
def get_token(user_id):
    """API endpoint for bot to retrieve user tokens"""
    tokens = load_tokens()
    token = tokens.get(user_id)
    
    if token:
        return jsonify({"success": True, "token": token})
    else:
        return jsonify({"success": False, "error": "User not authorized"}), 404

@app.route("/api/all_users")
def get_all_users():
    """Get all authorized users for the pull command"""
    tokens = load_tokens()
    users = [{"user_id": uid, "token": token} for uid, token in tokens.items()]
    return jsonify({"users": users})


@app.route("/api/health")
def health():
    """Health check with config status"""
    return jsonify({
        "status": "healthy",
        "config": {
            "client_id_set": bool(CLIENT_ID),
            "client_secret_set": bool(CLIENT_SECRET),
            "redirect_uri_set": bool(REDIRECT_URI),
            "redirect_uri": REDIRECT_URI  # Safe to show
        }
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
