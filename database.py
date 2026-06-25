import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "memoires.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS specializations (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS titles (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        name              TEXT NOT NULL,
        specialization_id INTEGER NOT NULL REFERENCES specializations(id) ON DELETE CASCADE,
        is_taken          INTEGER NOT NULL DEFAULT 0,
        is_suggested      INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS supervisors (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT NOT NULL UNIQUE,
        max_students  INTEGER NOT NULL DEFAULT 3,
        current_count INTEGER NOT NULL DEFAULT 0,
        is_suggested  INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS registrations (
        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
        student1_first     TEXT NOT NULL,
        student1_last      TEXT NOT NULL,
        student1_email     TEXT NOT NULL UNIQUE,
        student2_first     TEXT,
        student2_last      TEXT,
        student2_email     TEXT UNIQUE,
        is_solo            INTEGER NOT NULL DEFAULT 0,
        specialization_id  INTEGER REFERENCES specializations(id),
        title_id           INTEGER REFERENCES titles(id),
        custom_title       TEXT,
        supervisor_id      INTEGER REFERENCES supervisors(id),
        custom_supervisor  TEXT,
        notes              TEXT,
        change_request     TEXT,
        created_at         TEXT NOT NULL,
        updated_at         TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()

# ── Specializations ────────────────────────────────────────────────────────────

def get_specializations():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM specializations ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_specialization(name):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO specializations (name) VALUES (?)", (name.strip(),))
        conn.commit()
        return True, "تمت الإضافة بنجاح"
    except sqlite3.IntegrityError:
        return False, "التخصص موجود بالفعل"
    finally:
        conn.close()

def delete_specialization(spec_id):
    conn = get_conn()
    conn.execute("DELETE FROM specializations WHERE id=?", (spec_id,))
    conn.commit()
    conn.close()

# ── Titles ─────────────────────────────────────────────────────────────────────

def get_titles(spec_id, available_only=True):
    conn = get_conn()
    q = "SELECT * FROM titles WHERE specialization_id=?"
    params = [spec_id]
    if available_only:
        q += " AND is_taken=0"
    q += " ORDER BY name"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_titles():
    conn = get_conn()
    rows = conn.execute("""
        SELECT t.*, s.name as spec_name
        FROM titles t JOIN specializations s ON t.specialization_id = s.id
        ORDER BY s.name, t.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_title(name, spec_id):
    conn = get_conn()
    conn.execute("INSERT INTO titles (name, specialization_id) VALUES (?,?)", (name.strip(), spec_id))
    conn.commit()
    conn.close()

def delete_title(title_id):
    conn = get_conn()
    taken = conn.execute("SELECT is_taken FROM titles WHERE id=?", (title_id,)).fetchone()
    if taken and taken["is_taken"]:
        conn.close()
        return False, "لا يمكن حذف عنوان محجوز"
    conn.execute("DELETE FROM titles WHERE id=?", (title_id,))
    conn.commit()
    conn.close()
    return True, "تم الحذف"

def release_title(title_id):
    conn = get_conn()
    conn.execute("UPDATE titles SET is_taken=0 WHERE id=?", (title_id,))
    conn.commit()
    conn.close()

# ── Supervisors ────────────────────────────────────────────────────────────────

def get_supervisors(available_only=True):
    conn = get_conn()
    if available_only:
        rows = conn.execute(
            "SELECT * FROM supervisors WHERE current_count < max_students ORDER BY name"
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM supervisors ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_supervisor(name, max_students=3):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO supervisors (name, max_students) VALUES (?,?)",
            (name.strip(), max_students)
        )
        conn.commit()
        return True, "تمت الإضافة بنجاح"
    except sqlite3.IntegrityError:
        return False, "المشرف موجود بالفعل"
    finally:
        conn.close()

def update_supervisor_max(sup_id, new_max):
    conn = get_conn()
    conn.execute("UPDATE supervisors SET max_students=? WHERE id=?", (new_max, sup_id))
    conn.commit()
    conn.close()

def delete_supervisor(sup_id):
    conn = get_conn()
    row = conn.execute("SELECT current_count FROM supervisors WHERE id=?", (sup_id,)).fetchone()
    if row and row["current_count"] > 0:
        conn.close()
        return False, "لا يمكن حذف مشرف لديه طلاب مسجلون"
    conn.execute("DELETE FROM supervisors WHERE id=?", (sup_id,))
    conn.commit()
    conn.close()
    return True, "تم الحذف"

# ── Registrations ──────────────────────────────────────────────────────────────

def solo_count():
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM registrations WHERE is_solo=1").fetchone()[0]
    conn.close()
    return n

def email_exists(email):
    conn = get_conn()
    e = email.strip().lower()
    r = conn.execute(
        "SELECT id FROM registrations WHERE student1_email=? OR student2_email=?", (e, e)
    ).fetchone()
    conn.close()
    return r is not None

def register_student(data):
    """data: dict with all form fields. Returns (ok, message)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email1 = data["student1_email"].strip().lower()
    email2 = data.get("student2_email", "").strip().lower() or None

    # Validate emails uniqueness
    if email_exists(email1):
        return False, "البريد الإلكتروني للطالب الأول مسجل مسبقاً"
    if email2 and email_exists(email2):
        return False, "البريد الإلكتروني للطالب الثاني مسجل مسبقاً"
    if email2 and email1 == email2:
        return False, "لا يمكن أن يكون بريد الطالبين متطابقاً"

    is_solo = data.get("is_solo", False)
    if is_solo and solo_count() >= 15:
        return False, "امتلأت مقاعد التسجيل الفردي (15 مقعداً)"

    conn = get_conn()
    try:
        # Handle title
        title_id = data.get("title_id") or None
        custom_title = data.get("custom_title", "").strip() or None

        if title_id:
            row = conn.execute("SELECT is_taken FROM titles WHERE id=?", (title_id,)).fetchone()
            if not row or row["is_taken"]:
                return False, "هذا العنوان محجوز بالفعل"
            conn.execute("UPDATE titles SET is_taken=1 WHERE id=?", (title_id,))
            custom_title = None
        elif custom_title:
            conn.execute(
                "INSERT INTO titles (name, specialization_id, is_taken, is_suggested) VALUES (?,?,1,1)",
                (custom_title, data["specialization_id"])
            )
            title_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            custom_title = None
        else:
            return False, "يجب اختيار عنوان أو اقتراح عنوان"

        # Handle supervisor
        sup_id = data.get("supervisor_id") or None
        custom_sup = data.get("custom_supervisor", "").strip() or None

        if sup_id:
            row = conn.execute(
                "SELECT current_count, max_students FROM supervisors WHERE id=?", (sup_id,)
            ).fetchone()
            if not row or row["current_count"] >= row["max_students"]:
                return False, "هذا المشرف وصل للحد الأقصى"
            conn.execute("UPDATE supervisors SET current_count=current_count+1 WHERE id=?", (sup_id,))
            custom_sup = None
        elif custom_sup:
            conn.execute(
                "INSERT INTO supervisors (name, max_students, current_count, is_suggested) VALUES (?,3,1,1)",
                (custom_sup,)
            )
            sup_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            custom_sup = None
        else:
            return False, "يجب اختيار مشرف أو اقتراح مشرف"

        conn.execute("""
            INSERT INTO registrations (
                student1_first, student1_last, student1_email,
                student2_first, student2_last, student2_email,
                is_solo, specialization_id,
                title_id, custom_title,
                supervisor_id, custom_supervisor,
                notes, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["student1_first"].strip(), data["student1_last"].strip(), email1,
            data.get("student2_first","").strip() or None,
            data.get("student2_last","").strip() or None,
            email2,
            1 if is_solo else 0,
            data["specialization_id"],
            title_id, custom_sup,
            sup_id, None,
            data.get("notes","").strip() or None,
            now, now
        ))
        conn.commit()
        return True, "تم التسجيل بنجاح ✅"
    except Exception as e:
        conn.rollback()
        return False, f"خطأ: {str(e)}"
    finally:
        conn.close()

def get_registration_by_email(email):
    email = email.strip().lower()
    conn = get_conn()
    row = conn.execute("""
        SELECT r.*,
               s.name  as spec_name,
               t.name  as title_name,
               sv.name as supervisor_name
        FROM registrations r
        LEFT JOIN specializations s  ON r.specialization_id = s.id
        LEFT JOIN titles t           ON r.title_id = t.id
        LEFT JOIN supervisors sv     ON r.supervisor_id = sv.id
        WHERE r.student1_email=? OR r.student2_email=?
    """, (email, email)).fetchone()
    conn.close()
    return dict(row) if row else None

def submit_change_request(email, request_text):
    email = email.strip().lower()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    c = conn.execute(
        "UPDATE registrations SET change_request=?, updated_at=? WHERE student1_email=? OR student2_email=?",
        (request_text.strip(), now, email, email)
    )
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0

def get_all_registrations():
    conn = get_conn()
    rows = conn.execute("""
        SELECT r.*,
               s.name  as spec_name,
               t.name  as title_name,
               sv.name as supervisor_name
        FROM registrations r
        LEFT JOIN specializations s  ON r.specialization_id = s.id
        LEFT JOIN titles t           ON r.title_id = t.id
        LEFT JOIN supervisors sv     ON r.supervisor_id = sv.id
        ORDER BY r.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_registration(reg_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM registrations WHERE id=?", (reg_id,)).fetchone()
    if not row:
        conn.close()
        return False, "التسجيل غير موجود"
    row = dict(row)
    if row["supervisor_id"]:
        conn.execute(
            "UPDATE supervisors SET current_count=MAX(0,current_count-1) WHERE id=?",
            (row["supervisor_id"],)
        )
    if row["title_id"]:
        conn.execute("UPDATE titles SET is_taken=0 WHERE id=?", (row["title_id"],))
    conn.execute("DELETE FROM registrations WHERE id=?", (reg_id,))
    conn.commit()
    conn.close()
    return True, "تم الحذف"

def get_stats():
    conn = get_conn()
    total      = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
    solo       = conn.execute("SELECT COUNT(*) FROM registrations WHERE is_solo=1").fetchone()[0]
    chg_req    = conn.execute("SELECT COUNT(*) FROM registrations WHERE change_request IS NOT NULL AND change_request!=''").fetchone()[0]
    sups       = conn.execute("SELECT * FROM supervisors ORDER BY name").fetchall()
    conn.close()
    return {
        "total": total, "solo": solo, "duo": total - solo,
        "solo_remaining": max(0, 15 - solo),
        "change_requests": chg_req,
        "supervisors": [dict(s) for s in sups],
    }
