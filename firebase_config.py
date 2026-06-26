# firebase_config.py
import os
from dotenv import load_dotenv
import pyrebase
import streamlit as st

# تحميل المتغيرات من .env (للتشغيل المحلي)
load_dotenv()

# إعدادات Firebase
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY", st.secrets.get("firebase", {}).get("apiKey", "")),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", st.secrets.get("firebase", {}).get("authDomain", "")),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", st.secrets.get("firebase", {}).get("projectId", "")),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", st.secrets.get("firebase", {}).get("storageBucket", "")),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", st.secrets.get("firebase", {}).get("messagingSenderId", "")),
    "appId": os.getenv("FIREBASE_APP_ID", st.secrets.get("firebase", {}).get("appId", "")),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL", st.secrets.get("firebase", {}).get("databaseURL", ""))
}

# تهيئة Firebase
try:
    firebase = pyrebase.initialize_app(firebase_config)
    db = firebase.database()
    auth = firebase.auth()
    print("✅ Firebase connected successfully!")
except Exception as e:
    print(f"❌ Firebase connection error: {e}")
    db = None
    auth = None
