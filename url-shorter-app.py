from flask import Flask, request, redirect, jsonify, Response
import json
import os
import hashlib
import time

app = Flask(__name__)

DB_FILE = "data.json"


# ---------- Helpers ----------
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)


def generate_code(url):
    return hashlib.md5(url.encode()).hexdigest()[:6]


# ---------- Minimal Frontend ----------
@app.route("/", methods=["GET"])
def home():
    return Response(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>URL Shortener</title>
        <style>
            body {{
                font-family: Arial;
                max-width: 500px;
                margin: 60px auto;
                text-align: center;
            }}
            input, button {{
                padding: 10px;
                margin: 5px;
                width: 80%;
            }}
        </style>
    </head>
    <body>
        <h2>🔗 URL Shortener</h2>
        <form method="POST" action="/shorten">
            <input name="url" placeholder="Enter URL" required /><br>
            <input name="expiry_seconds" placeholder="Expiry (seconds, optional)" /><br>
            <button type="submit">Shorten</button>
        </form>
    </body>
    </html>
    """, mimetype="text/html")


# ---------- Shorten ----------
@app.route("/shorten", methods=["POST"])
def shorten():
    # Works for BOTH JSON API + HTML form
    if request.is_json:
        data = request.get_json()
        url = data.get("url")
        expiry_seconds = data.get("expiry_seconds")
    else:
        url = request.form.get("url")
        expiry_seconds = request.form.get("expiry_seconds")

    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    code = generate_code(url)
    db = load_db()

    expiry_time = None
    if expiry_seconds:
        try:
            expiry_time = int(time.time()) + int(expiry_seconds)
        except:
            pass

    db[code] = {
        "url": url,
        "expiry": expiry_time
    }

    save_db(db)

    short_url = f"/{code}"

    # If browser → return HTML
    if not request.is_json:
        return Response(f"""
        <html>
        <body style="font-family: Arial; text-align:center; margin-top:50px;">
            <h3>✅ Short URL Created</h3>
            <p><a href="{short_url}">{short_url}</a></p>
            <br>
            <a href="/">⬅ Back</a>
        </body>
        </html>
        """, mimetype="text/html")

    # If API → return JSON
    return jsonify({
        "short_url": short_url,
        "code": code,
        "expires_at": expiry_time
    })


# ---------- Redirect ----------
@app.route("/<code>")
def redirect_url(code):
    db = load_db()

    if code not in db:
        return "Invalid code", 404

    entry = db[code]

    if entry["expiry"] and time.time() > entry["expiry"]:
        return "Link expired", 410

    return redirect(entry["url"])


# ---------- Run ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)