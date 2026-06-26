import streamlit as st
import base64, os
from database import (
    init_db, get_specializations, add_specialization, delete_specialization,
    get_titles, get_all_titles, add_title, delete_title, release_title,
    get_supervisors, add_supervisor, update_supervisor_max, delete_supervisor,
    register_student, get_registration_by_email, submit_change_request,
    get_all_registrations, delete_registration, get_stats, solo_count, get_conn,
)
from excel_export import export_to_excel
from datetime import datetime
#
# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="تسجيل مذكرات التخرج",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; }
.main { background: linear-gradient(135deg, #f0f4ff 0%, #fafafa 100%); }
.stButton > button {
    border-radius: 12px !important; font-weight: 700 !important;
    font-family: 'Cairo', sans-serif !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important; }
.stSelectbox > div, .stTextInput > div > div, .stTextArea > div > div { border-radius: 10px !important; }
.card { background:white; border-radius:16px; padding:24px; margin-bottom:20px;
        box-shadow:0 2px 12px rgba(0,0,0,0.06); border:1px solid #e8eef5; }
.card-blue  { border-right: 5px solid #1E3A8A; }
.card-green { border-right: 5px solid #16a34a; }
.card-amber { border-right: 5px solid #d97706; }
.card-red   { border-right: 5px solid #dc2626; }
.header-banner {
    background: linear-gradient(135deg, #1E3A8A, #2563EB);
    color: white; padding: 0; border-radius: 18px;
    margin-bottom: 28px; overflow: hidden;
}
.header-content { padding: 24px 32px; text-align: center; }
.header-banner h1 { color: white; margin: 0; font-size: 1.7rem; }
.header-banner p  { color: #bfdbfe; margin: 6px 0 0; font-size: 0.9rem; }
.logos-row { display:flex; justify-content:center; align-items:center;
             gap:20px; padding:16px 32px 0; }
.logos-row img { height:75px; width:75px; object-fit:contain;
                 border-radius:50%; background:white; padding:4px;
                 box-shadow:0 2px 8px rgba(0,0,0,0.2); }
.stat-box { background:white; border-radius:14px; padding:18px; text-align:center;
            box-shadow:0 2px 8px rgba(0,0,0,0.08); border-top:4px solid #2563EB; }
.stat-num  { font-size:2rem; font-weight:700; color:#1E3A8A; line-height:1.1; }
.stat-lbl  { color:#64748b; font-size:0.85rem; margin-top:4px; }
.badge-solo { background:#dcfce7; color:#15803d; padding:2px 10px; border-radius:20px; font-size:0.8rem; font-weight:600; }
.badge-duo  { background:#dbeafe; color:#1d4ed8; padding:2px 10px; border-radius:20px; font-size:0.8rem; font-weight:600; }
.step-bar { display:flex; gap:6px; margin-bottom:20px; }
.step-done { flex:1; height:6px; border-radius:3px; background:#2563EB; }
.step-todo { flex:1; height:6px; border-radius:3px; background:#e2e8f0; }
div[data-testid="stExpander"] { border-radius:12px !important; border:1px solid #e2e8f0 !important; }
.stAlert { border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────
init_db()

# كلمة المرور — تعمل مع secrets.toml أو بدونه

ADMIN_PASSWORD = "Osama2b0a1h3i"

# ── Helper: encode image to base64 ────────────────────────────────────────────
def img_to_b64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

# ── Header with logos ──────────────────────────────────────────────────────────
logo1_path = os.path.join(os.path.dirname(__file__), "logo_univ.png")
logo2_path = os.path.join(os.path.dirname(__file__), "logo_faculty.png")
b64_1 = img_to_b64(logo1_path)
b64_2 = img_to_b64(logo2_path)

logos_html = ""
if b64_1 or b64_2:
    imgs = ""
    if b64_1: imgs += f'<img src="data:image/png;base64,{b64_1}" alt="شعار الجامعة"/>'
    if b64_2: imgs += f'<img src="data:image/png;base64,{b64_2}" alt="شعار الكلية"/>'
    logos_html = f'<div class="logos-row">{imgs}</div>'

st.markdown(f"""
<div class="header-banner">
  {logos_html}
  <div class="header-content">
    <h1>🎓 منصة تسجيل مذكرات التخرج</h1>
    <p>كلية العلوم الإسلامية — التسجيل الإلكتروني لمذكرات الماستر</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Navigation ─────────────────────────────────────────────────────────────────
tabs = st.tabs(["📝 التسجيل", "🔍 الاستعلام", "✏️ طلب تغيير", "🔐 الإدارة"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Registration
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    if "reg_step" not in st.session_state:
        st.session_state.reg_step = 1
    if "reg_data" not in st.session_state:
        st.session_state.reg_data = {}

    step = st.session_state.reg_step
    bars = "".join([f'<div class="{"step-done" if i<=step else "step-todo"}"></div>' for i in range(1,4)])
    labels = {1:"بيانات الطلاب", 2:"التخصص والعنوان", 3:"المشرف والتأكيد"}
    st.markdown(f'<div class="step-bar">{bars}</div><p style="color:#64748b;font-size:0.9rem;margin-bottom:16px">الخطوة {step} من 3 — <strong>{labels[step]}</strong></p>', unsafe_allow_html=True)

    if step == 1:
        with st.container():
            st.markdown('<div class="card card-blue">', unsafe_allow_html=True)
            solo_used = solo_count()
            solo_left = max(0, 15 - solo_used)
            st.markdown("#### 📋 نوع التسجيل")
            is_solo = st.radio("نوع التسجيل", options=[False, True],
                format_func=lambda x: f"فردي 👤  (متبقي {solo_left}/15)" if x else "ثنائي 👥 (الأغلبية)",
                horizontal=True, disabled=(solo_left==0), label_visibility="collapsed")
            st.markdown("---")
            st.markdown("#### 👤 الطالب الأول")
            c1,c2 = st.columns(2)
            with c1: s1_last  = st.text_input("اللقب *", key="s1_last")
            with c2: s1_first = st.text_input("الاسم *", key="s1_first")
            s1_email = st.text_input("البريد الإلكتروني *", key="s1_email", placeholder="example@univ-eloued.dz")
            s2_last = s2_first = s2_email = ""
            if not is_solo:
                st.markdown("---")
                st.markdown("#### 👤 الطالب الثاني (الزميل)")
                c3,c4 = st.columns(2)
                with c3: s2_last  = st.text_input("اللقب *", key="s2_last")
                with c4: s2_first = st.text_input("الاسم *", key="s2_first")
                s2_email = st.text_input("البريد الإلكتروني *", key="s2_email", placeholder="example@univ-eloued.dz")
            st.markdown('</div>', unsafe_allow_html=True)
            if st.button("التالي ◄", type="primary", use_container_width=True):
                errors = []
                if not s1_last.strip() or not s1_first.strip(): errors.append("يرجى إدخال اسم ولقب الطالب الأول")
                if not s1_email.strip() or "@" not in s1_email: errors.append("يرجى إدخال بريد إلكتروني صحيح للطالب الأول")
                if not is_solo:
                    if not s2_last.strip() or not s2_first.strip(): errors.append("يرجى إدخال اسم ولقب الزميل")
                    if not s2_email.strip() or "@" not in s2_email: errors.append("يرجى إدخال بريد إلكتروني صحيح للزميل")
                    if s1_email.strip().lower() == s2_email.strip().lower(): errors.append("لا يمكن أن يتطابق بريد الطالبين")
                if errors:
                    for e in errors: st.error(e)
                else:
                    st.session_state.reg_data.update({
                        "student1_first":s1_first,"student1_last":s1_last,"student1_email":s1_email,
                        "student2_first":s2_first,"student2_last":s2_last,
                        "student2_email":s2_email if not is_solo else "","is_solo":is_solo,
                    })
                    st.session_state.reg_step = 2; st.rerun()

    elif step == 2:
        with st.container():
            st.markdown('<div class="card card-blue">', unsafe_allow_html=True)
            st.markdown("#### 📚 التخصص")
            specs = get_specializations()
            if not specs:
                st.warning("⚠️ لم يتم إضافة أي تخصص بعد. تواصل مع الإدارة."); st.stop()
            spec_options = {s["name"]: s["id"] for s in specs}
            spec_name = st.selectbox("اختر التخصص *", options=list(spec_options.keys()))
            spec_id   = spec_options[spec_name]
            st.markdown("---")
            st.markdown("#### 📄 عنوان المذكرة")
            available_titles = get_titles(spec_id, available_only=True)
            title_id = None; custom_title = ""
            if available_titles:
                title_opts = ["-- اقتراح عنوان جديد --"] + [t["name"] for t in available_titles]
                chosen = st.selectbox("اختر عنواناً من القائمة", options=title_opts)
                if chosen != "-- اقتراح عنوان جديد --":
                    title_id = next(t["id"] for t in available_titles if t["name"] == chosen)
                    st.info(f"✅ العنوان المختار: **{chosen}**")
            else:
                st.info("ℹ️ لا توجد عناوين متاحة في هذا التخصص. يمكنك اقتراح عنوان.")
            if not title_id:
                custom_title = st.text_area("اقترح عنواناً جديداً *", placeholder="اكتب عنوان مذكرتك المقترح هنا...", height=90)
            st.markdown('</div>', unsafe_allow_html=True)
            col_back, col_next = st.columns(2)
            with col_back:
                if st.button("► السابق", use_container_width=True):
                    st.session_state.reg_step = 1; st.rerun()
            with col_next:
                if st.button("التالي ◄", type="primary", use_container_width=True):
                    if not title_id and not custom_title.strip():
                        st.error("يرجى اختيار عنوان أو كتابة عنوان مقترح")
                    else:
                        st.session_state.reg_data.update({"specialization_id":spec_id,"title_id":title_id,"custom_title":custom_title.strip()})
                        st.session_state.reg_step = 3; st.rerun()

    elif step == 3:
        with st.container():
            st.markdown('<div class="card card-blue">', unsafe_allow_html=True)
            st.markdown("#### 👨‍🏫 المشرف")
            available_sups = get_supervisors(available_only=True)
            sup_id = None; custom_sup = ""
            if available_sups:
                sup_opts = ["-- اقتراح مشرف جديد --"] + [f"{s['name']}  (متبقي: {s['max_students']-s['current_count']})" for s in available_sups]
                chosen_sup = st.selectbox("اختر مشرفاً من القائمة", options=sup_opts)
                if chosen_sup != "-- اقتراح مشرف جديد --":
                    idx = sup_opts.index(chosen_sup) - 1
                    sup_id = available_sups[idx]["id"]
            else:
                st.warning("⚠️ جميع المشرفين وصلوا للحد الأقصى. يمكنك اقتراح مشرف.")
            if not sup_id:
                custom_sup = st.text_input("اقترح مشرفاً جديداً *", placeholder="أ.د / د. اسم المشرف المقترح")
            notes = st.text_area("ملاحظات إضافية (اختياري)", height=80)
            st.markdown('</div>', unsafe_allow_html=True)

            d = st.session_state.reg_data
            specs_all = get_specializations()
            spec_name2 = next((s["name"] for s in specs_all if s["id"]==d.get("specialization_id")),"")
            titles_all2 = get_titles(d.get("specialization_id",""), available_only=False) if d.get("specialization_id") else []
            title_name2 = next((t["name"] for t in titles_all2 if t["id"]==d.get("title_id")), d.get("custom_title",""))
            st.markdown(f"""
            <div class="card card-green">
            <p style="font-weight:700;font-size:1rem;margin-bottom:12px">📌 ملخص التسجيل</p>
            <table style="width:100%;border-collapse:collapse;font-size:0.9rem">
              <tr><td style="color:#64748b;width:35%;padding:4px 0">الطالب الأول</td>
                  <td><b>{d.get('student1_last','')} {d.get('student1_first','')}</b> — {d.get('student1_email','')}</td></tr>
              {'<tr><td style="color:#64748b;padding:4px 0">الطالب الثاني</td><td><b>'+d.get("student2_last","")+" "+d.get("student2_first","")+'</b> — '+d.get("student2_email","")+'</td></tr>' if not d.get("is_solo") else ''}
              <tr><td style="color:#64748b;padding:4px 0">نوع التسجيل</td>
                  <td><span class="{'badge-solo' if d.get('is_solo') else 'badge-duo'}">{'فردي' if d.get('is_solo') else 'ثنائي'}</span></td></tr>
              <tr><td style="color:#64748b;padding:4px 0">التخصص</td><td>{spec_name2}</td></tr>
              <tr><td style="color:#64748b;padding:4px 0">العنوان</td><td>{title_name2} {'<span style="color:#d97706;font-size:0.8rem">(مقترح)</span>' if d.get('custom_title') else ''}</td></tr>
            </table>
            </div>
            """, unsafe_allow_html=True)

            col_back2, col_submit = st.columns(2)
            with col_back2:
                if st.button("► السابق", use_container_width=True):
                    st.session_state.reg_step = 2; st.rerun()
            with col_submit:
                if st.button("✅ تأكيد التسجيل", type="primary", use_container_width=True):
                    if not sup_id and not custom_sup.strip():
                        st.error("يرجى اختيار مشرف أو كتابة اسم مشرف مقترح")
                    else:
                        payload = {**d, "supervisor_id":sup_id, "custom_supervisor":custom_sup, "notes":notes}
                        ok, msg = register_student(payload)
                        if ok:
                            st.balloons(); st.success(msg)
                            st.info("🔑 احتفظ ببريدك الإلكتروني للاستعلام عن تسجيلك لاحقاً.")
                            st.session_state.reg_step = 1; st.session_state.reg_data = {}
                        else:
                            st.error(f"⚠️ {msg}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Check Registration
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("### 🔍 الاستعلام عن تسجيلك")
    st.markdown('<div class="card card-blue">', unsafe_allow_html=True)
    email_check = st.text_input("أدخل بريدك الإلكتروني", placeholder="example@univ-eloued.dz", key="check_email")
    if st.button("استعلام", type="primary", key="btn_check"):
        if not email_check.strip():
            st.warning("يرجى إدخال البريد الإلكتروني")
        else:
            reg = get_registration_by_email(email_check)
            if not reg:
                st.error("❌ لا يوجد تسجيل مرتبط بهذا البريد الإلكتروني")
            else:
                title = reg.get("title_name") or reg.get("custom_title") or "—"
                sup   = reg.get("supervisor_name") or reg.get("custom_supervisor") or "—"
                st.success("✅ وُجد تسجيلك")
                st.markdown(f"""
                <div class="card card-green" style="margin-top:16px">
                <table style="width:100%;border-collapse:collapse;font-size:0.92rem;line-height:2">
                  <tr><td style="color:#64748b;width:35%">الطالب الأول</td><td><b>{reg['student1_last']} {reg['student1_first']}</b></td></tr>
                  <tr><td style="color:#64748b">الطالب الثاني</td><td>{(reg.get('student2_last') or '')+" "+(reg.get('student2_first') or '') or '—'}</td></tr>
                  <tr><td style="color:#64748b">نوع التسجيل</td><td><span class="{'badge-solo' if reg['is_solo'] else 'badge-duo'}">{'فردي' if reg['is_solo'] else 'ثنائي'}</span></td></tr>
                  <tr><td style="color:#64748b">التخصص</td><td>{reg.get('spec_name') or '—'}</td></tr>
                  <tr><td style="color:#64748b">العنوان</td><td>{title}</td></tr>
                  <tr><td style="color:#64748b">المشرف</td><td>{sup}</td></tr>
                  <tr><td style="color:#64748b">ملاحظات</td><td>{reg.get('notes') or '—'}</td></tr>
                  <tr><td style="color:#64748b">تاريخ التسجيل</td><td>{reg.get('created_at','')}</td></tr>
                  {'<tr><td style="color:#d97706">طلب التغيير</td><td style="color:#d97706">'+reg["change_request"]+'</td></tr>' if reg.get('change_request') else ''}
                </table>
                </div>
                """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Change Request
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("### ✏️ طلب تغيير")
    st.info("يمكنك تقديم طلب تغيير المشرف أو العنوان أو الزميل. سيتم مراجعة طلبك من قِبَل الإدارة.")
    st.markdown('<div class="card card-amber">', unsafe_allow_html=True)
    chg_email   = st.text_input("بريدك الإلكتروني *", placeholder="example@univ-eloued.dz", key="chg_email")
    chg_type    = st.selectbox("نوع الطلب", ["طلب تغيير المشرف","طلب تغيير عنوان المذكرة","طلب تغيير الزميل","شكوى أو ملاحظة أخرى"])
    chg_details = st.text_area("تفاصيل الطلب *", placeholder="اشرح طلبك بوضوح...", height=120)
    if st.button("📨 إرسال الطلب", type="primary", key="btn_chg"):
        if not chg_email.strip() or "@" not in chg_email:
            st.error("يرجى إدخال بريد إلكتروني صحيح")
        elif not chg_details.strip():
            st.error("يرجى كتابة تفاصيل الطلب")
        else:
            ok = submit_change_request(chg_email, f"[{chg_type}]\n{chg_details.strip()}")
            if ok: st.success("✅ تم إرسال طلبك بنجاح. ستُراجعه الإدارة وتتواصل معك.")
            else:  st.error("❌ لا يوجد تسجيل بهذا البريد الإلكتروني")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Admin Panel
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    if "admin_ok" not in st.session_state:
        st.session_state.admin_ok = False

    if not st.session_state.admin_ok:
        st.markdown("### 🔐 تسجيل دخول الإدارة")
        st.markdown('<div class="card card-red">', unsafe_allow_html=True)
        pwd = st.text_input("كلمة المرور", type="password", key="admin_pwd")
        if st.button("دخول", type="primary"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_ok = True; st.rerun()
            else:
                st.error("❌ كلمة المرور غير صحيحة")
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        col_logout, _ = st.columns([1, 4])
        with col_logout:
            if st.button("خروج 🚪"):
                st.session_state.admin_ok = False; st.rerun()

        st.markdown("## 🛠️ لوحة الإدارة")

        # Stats
        stats = get_stats()
        c1,c2,c3,c4 = st.columns(4)
        for col, (num,lbl) in zip([c1,c2,c3,c4],[
            (stats["total"],"إجمالي التسجيلات"),
            (stats["solo"],f"فردي (متبقي {stats['solo_remaining']})"),
            (stats["duo"],"ثنائي"),
            (stats["change_requests"],"طلبات التغيير")
        ]):
            with col:
                st.markdown(f'<div class="stat-box"><div class="stat-num">{num}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        admin_tabs = st.tabs(["🗂️ التخصصات والعناوين", "👨‍🏫 المشرفون", "📋 التسجيلات", "📥 تصدير Excel", "🖼️ الشعارات"])

        # ── Tab 1: Specs & Titles ──────────────────────────────────────────────
        with admin_tabs[0]:
            col_l, col_r = st.columns([1,1])
            with col_l:
                st.markdown("#### إضافة تخصص")
                new_spec = st.text_input("اسم التخصص", key="new_spec")
                if st.button("➕ إضافة تخصص", use_container_width=True):
                    ok, msg = add_specialization(new_spec)
                    (st.success if ok else st.error)(msg)
                    if ok: st.rerun()
                st.markdown("#### التخصصات الحالية")
                for s in get_specializations():
                    sc1,sc2 = st.columns([3,1])
                    with sc1: st.write(f"📌 {s['name']}")
                    with sc2:
                        if st.button("حذف", key=f"del_spec_{s['id']}"):
                            delete_specialization(s["id"]); st.rerun()
            with col_r:
                st.markdown("#### إضافة عنوان")
                specs2 = get_specializations()
                if specs2:
                    sp_map = {s["name"]:s["id"] for s in specs2}
                    chosen_sp = st.selectbox("التخصص", list(sp_map.keys()), key="sp4title")
                    new_title = st.text_area("العنوان", key="new_title", height=80)
                    if st.button("➕ إضافة عنوان", use_container_width=True):
                        if new_title.strip():
                            add_title(new_title.strip(), sp_map[chosen_sp])
                            st.success("تمت الإضافة"); st.rerun()
                st.markdown("#### العناوين الحالية")
                for t in get_all_titles():
                    tc1,tc2,tc3 = st.columns([3,1,1])
                    with tc1:
                        status = "🔴 محجوز" if t["is_taken"] else "🟢 متاح"
                        sug    = " *(مقترح)*" if t["is_suggested"] else ""
                        st.caption(f"{status} — {t['name'][:55]}{sug}")
                    with tc2:
                        if t["is_taken"] and st.button("تحرير", key=f"rel_{t['id']}"):
                            release_title(t["id"]); st.rerun()
                    with tc3:
                        if not t["is_taken"] and st.button("حذف", key=f"del_t_{t['id']}"):
                            ok, msg = delete_title(t["id"])
                            (st.success if ok else st.error)(msg)
                            if ok: st.rerun()

        # ── Tab 2: Supervisors ─────────────────────────────────────────────────
        with admin_tabs[1]:
            col_l2, col_r2 = st.columns([1,1])
            with col_l2:
                st.markdown("#### إضافة مشرف")
                new_sup_name = st.text_input("اسم المشرف", key="new_sup")
                new_sup_max  = st.number_input("الحد الأقصى للمذكرات", min_value=1, max_value=10, value=3, key="sup_max")
                if st.button("➕ إضافة مشرف", use_container_width=True):
                    ok, msg = add_supervisor(new_sup_name, new_sup_max)
                    (st.success if ok else st.error)(msg)
                    if ok: st.rerun()
            with col_r2:
                st.markdown("#### المشرفون الحاليون")
                for s in get_supervisors(available_only=False):
                    remaining = s["max_students"] - s["current_count"]
                    color = "#16a34a" if remaining > 0 else "#dc2626"
                    sc1,sc2,sc3 = st.columns([3,1,1])
                    with sc1:
                        st.markdown(f"**{s['name']}** &nbsp;<span style='color:{color};font-size:0.8rem'>({s['current_count']}/{s['max_students']})</span>{'&nbsp;*(مقترح)*' if s['is_suggested'] else ''}", unsafe_allow_html=True)
                    with sc2:
                        new_max = st.number_input("", min_value=s["current_count"], max_value=20,
                            value=s["max_students"], key=f"sup_mx_{s['id']}", label_visibility="collapsed")
                        if new_max != s["max_students"]:
                            update_supervisor_max(s["id"], new_max); st.rerun()
                    with sc3:
                        if st.button("حذف", key=f"del_sup_{s['id']}"):
                            ok, msg = delete_supervisor(s["id"])
                            (st.success if ok else st.error)(msg)
                            if ok: st.rerun()

        # ── Tab 3: Registrations ───────────────────────────────────────────────
        with admin_tabs[2]:
            regs = get_all_registrations()
            if not regs:
                st.info("لا توجد تسجيلات بعد.")
            else:
                # طلبات التغيير أولاً
                chg_regs = [r for r in regs if r.get("change_request")]
                if chg_regs:
                    st.markdown(f"#### ⚠️ طلبات التغيير ({len(chg_regs)})")
                    for r in chg_regs:
                        with st.expander(f"🔔 {r['student1_last']} {r['student1_first']} — {r.get('spec_name','')}"):
                            st.warning(f"**الطلب:** {r['change_request']}")
                            if st.button("✔️ تم المعالجة — مسح الطلب", key=f"clr_chg_{r['id']}"):
                                conn = get_conn()
                                conn.execute("UPDATE registrations SET change_request=NULL WHERE id=?", (r["id"],))
                                conn.commit(); conn.close(); st.rerun()
                    st.markdown("---")

                st.markdown(f"#### 📋 جميع التسجيلات ({len(regs)})")
                for r in regs:
                    title = r.get("title_name") or r.get("custom_title") or "—"
                    sup   = r.get("supervisor_name") or r.get("custom_supervisor") or "—"
                    badge = "🟡 فردي" if r["is_solo"] else "🔵 ثنائي"
                    chg_icon = " 🔔" if r.get("change_request") else ""
                    with st.expander(f"{badge}{chg_icon} | {r['student1_last']} {r['student1_first']} | {r.get('spec_name','')}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**الطالب 1:** {r['student1_last']} {r['student1_first']}")
                            st.write(f"**البريد 1:** {r['student1_email']}")
                            if not r["is_solo"]:
                                st.write(f"**الطالب 2:** {r.get('student2_last','')} {r.get('student2_first','')}")
                                st.write(f"**البريد 2:** {r.get('student2_email','') or '—'}")
                        with col_b:
                            st.write(f"**التخصص:** {r.get('spec_name','')}")
                            st.write(f"**العنوان:** {title}")
                            st.write(f"**المشرف:** {sup}")
                            st.write(f"**تاريخ التسجيل:** {r.get('created_at','')}")
                        if r.get("notes"):
                            st.write(f"**ملاحظات:** {r['notes']}")
                        if r.get("change_request"):
                            st.warning(f"🔔 **طلب التغيير:** {r['change_request']}")

                        st.markdown("---")
                        # ── زر الإلغاء وإعادة الإتاحة ──
                        st.markdown("**⚙️ إجراءات:**")
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("🗑️ إلغاء التسجيل وإعادة إتاحة العنوان والمشرف",
                                         key=f"del_reg_{r['id']}",
                                         help="سيُحذف التسجيل ويُحرَّر العنوان ويُخفَّض عداد المشرف"):
                                ok, msg = delete_registration(r["id"])
                                if ok:
                                    st.success(f"✅ {msg} — العنوان والمشرف متاحان الآن للطلاب")
                                    st.rerun()
                                else:
                                    st.error(msg)

        # ── Tab 4: Export Excel ────────────────────────────────────────────────
        with admin_tabs[3]:
            st.markdown("### 📥 تصدير بيانات التسجيلات")
            regs_all  = get_all_registrations()
            stats_all = get_stats()

            col_i1, col_i2, col_i3 = st.columns(3)
            with col_i1: st.metric("إجمالي التسجيلات", stats_all["total"])
            with col_i2: st.metric("فردي", stats_all["solo"])
            with col_i3: st.metric("ثنائي", stats_all["duo"])

            st.markdown("---")
            if regs_all:
                excel_data = export_to_excel(regs_all, stats_all)
                filename   = f"تسجيلات_المذكرات_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                st.download_button(
                    label="⬇️ تحميل ملف Excel الآن",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary",
                )
                st.caption(f"الملف يحتوي على {len(regs_all)} تسجيلاً + ورقة إحصائيات")
            else:
                st.info("لا توجد تسجيلات بعد للتصدير.")

        # ── Tab 5: Logos ───────────────────────────────────────────────────────
        with admin_tabs[4]:
            st.markdown("### 🖼️ إدارة الشعارات")
            st.info("ارفع صورة شعار الجامعة وشعار الكلية. الصيغ المقبولة: PNG أو JPG")

            app_dir = os.path.dirname(__file__)
            col_log1, col_log2 = st.columns(2)

            with col_log1:
                st.markdown("#### شعار الجامعة")
                up1 = st.file_uploader("ارفع شعار الجامعة", type=["png","jpg","jpeg"], key="up_univ")
                if up1:
                    with open(os.path.join(app_dir, "logo_univ.png"), "wb") as f:
                        f.write(up1.read())
                    st.success("✅ تم حفظ شعار الجامعة"); st.rerun()
                if os.path.exists(os.path.join(app_dir, "logo_univ.png")):
                    st.image(os.path.join(app_dir, "logo_univ.png"), width=120)
                    if st.button("🗑️ حذف شعار الجامعة"):
                        os.remove(os.path.join(app_dir, "logo_univ.png")); st.rerun()

            with col_log2:
                st.markdown("#### شعار الكلية")
                up2 = st.file_uploader("ارفع شعار الكلية", type=["png","jpg","jpeg"], key="up_fac")
                if up2:
                    with open(os.path.join(app_dir, "logo_faculty.png"), "wb") as f:
                        f.write(up2.read())
                    st.success("✅ تم حفظ شعار الكلية"); st.rerun()
                if os.path.exists(os.path.join(app_dir, "logo_faculty.png")):
                    st.image(os.path.join(app_dir, "logo_faculty.png"), width=120)
                    if st.button("🗑️ حذف شعار الكلية"):
                        os.remove(os.path.join(app_dir, "logo_faculty.png")); st.rerun()

            st.markdown("---")
            st.caption("بعد رفع الشعارات ستظهر تلقائياً في رأس الصفحة.")