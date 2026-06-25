# 🎓 منصة تسجيل مذكرات التخرج

## هيكل المشروع
```
memoires_app/
├── app.py              ← التطبيق الرئيسي (Streamlit)
├── database.py         ← قاعدة البيانات (SQLite)
├── excel_export.py     ← تصدير Excel
├── requirements.txt    ← المكتبات المطلوبة
└── .streamlit/
    ├── config.toml     ← إعدادات Streamlit
    └── secrets.toml    ← كلمة مرور الإدارة (لا ترفعه على GitHub)
```

---

## 🖥️ التشغيل المحلي (VSCode)

```bash
# 1. افتح المجلد في VSCode
cd memoires_app

# 2. أنشئ بيئة افتراضية
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Mac/Linux

# 3. ثبّت المكتبات
pip install -r requirements.txt

# 4. شغّل التطبيق
streamlit run app.py
```
سيفتح المتصفح تلقائياً على http://localhost:8501

---

## 🌐 النشر على Streamlit Cloud (مجاني)

1. ارفع المجلد على **GitHub** (احذف secrets.toml قبل الرفع)
2. اذهب إلى https://share.streamlit.io
3. اختر المستودع وملف `app.py`
4. من إعدادات التطبيق → **Secrets** أضف:
   ```toml
   ADMIN_PASSWORD = "كلمة_مرورك_القوية"
   ```
5. انشر وشارك الرابط مع الطلاب ✅

---

## 🔐 كلمة مرور الإدارة الافتراضية
`admin123` — **غيّرها حتماً قبل النشر**

---

## ✅ الميزات المدعومة

| الميزة | الحالة |
|--------|--------|
| تسجيل فردي (15 مقعداً) | ✅ |
| تسجيل ثنائي | ✅ |
| قوائم منسدلة ديناميكية | ✅ |
| تقييد المشرف بـ3 مذكرات | ✅ |
| إخفاء العناوين المحجوزة | ✅ |
| منع تكرار التسجيل بالبريد | ✅ |
| اقتراح عنوان/مشرف جديد | ✅ |
| طلبات التغيير | ✅ |
| الاستعلام بالبريد | ✅ |
| لوحة إدارة محمية | ✅ |
| تصدير Excel | ✅ |
| واجهة عربية RTL | ✅ |
