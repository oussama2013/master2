# firebase_config.py
import streamlit as st
import pyrebase

# إعدادات Firebase - كتابة الرابط مباشرة
firebase_config = {
    "apiKey": "AIzaSyCatHf0NlizimLq-FfAPGq4UYvMCHpCgwE",
    "authDomain": "master-tems.firebaseapp.com",
    "projectId": "master-tems",
    "storageBucket": "master-tems.firebasestorage.app",
    "messagingSenderId": "825388086153",
    "appId": "1:825388086153:web:2bfef6d4c99b4f3f82a758",
    "databaseURL": "https://master-tems-default-rtdb.firebaseio.com/"  # الرابط مكتوب مباشرة
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