# database.py - إصدار Firebase
import streamlit as st
from datetime import datetime
from firebase_config import db, auth
import uuid

# ============================================================
# دوال التخصصات (Specializations)
# ============================================================
def get_specializations():
    """جلب جميع التخصصات"""
    try:
        specs = db.child("specializations").get()
        if specs.each():
            return [{"id": spec.key(), "name": spec.val().get("name", "")} 
                    for spec in specs.each()]
        # بيانات افتراضية إذا كانت فارغة
        defaults = ["علم الحاسوب", "الرياضيات", "الفيزياء", "الكيمياء"]
        for name in defaults:
            db.child("specializations").push({"name": name})
        return [{"id": "default", "name": name} for name in defaults]
    except Exception as e:
        st.error(f"خطأ في جلب التخصصات: {str(e)}")
        return []

def add_specialization(name):
    """إضافة تخصص جديد"""
    try:
        if not name.strip():
            return False, "يرجى إدخال اسم التخصص"
        # التحقق من وجوده مسبقاً
        specs = db.child("specializations").order_by_child("name").equal_to(name.strip()).get()
        if specs.each():
            return False, "هذا التخصص موجود بالفعل"
        db.child("specializations").push({"name": name.strip()})
        return True, "تم إضافة التخصص بنجاح"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def delete_specialization(spec_id):
    """حذف تخصص"""
    try:
        db.child("specializations").child(spec_id).remove()
        return True
    except:
        return False

# ============================================================
# دوال العناوين (Titles)
# ============================================================
def get_titles(spec_id=None, available_only=True):
    """جلب العناوين حسب التخصص"""
    try:
        titles = db.child("titles").get()
        result = []
        if titles.each():
            for t in titles.each():
                data = t.val()
                if spec_id and data.get("specialization_id") != spec_id:
                    continue
                if available_only and data.get("is_taken", False):
                    continue
                result.append({
                    "id": t.key(),
                    "name": data.get("name", ""),
                    "specialization_id": data.get("specialization_id", ""),
                    "is_taken": data.get("is_taken", False),
                    "is_suggested": data.get("is_suggested", False)
                })
        return result
    except Exception as e:
        st.error(f"خطأ في جلب العناوين: {str(e)}")
        return []

def get_all_titles():
    """جلب جميع العناوين"""
    return get_titles(available_only=False)

def add_title(name, spec_id, is_suggested=False):
    """إضافة عنوان جديد"""
    try:
        if not name.strip():
            return False, "يرجى إدخال العنوان"
        db.child("titles").push({
            "name": name.strip(),
            "specialization_id": spec_id,
            "is_taken": False,
            "is_suggested": is_suggested
        })
        return True, "تم إضافة العنوان بنجاح"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def delete_title(title_id):
    """حذف عنوان"""
    try:
        title = db.child("titles").child(title_id).get()
        if title.val() and title.val().get("is_taken", False):
            return False, "لا يمكن حذف عنوان محجوز"
        db.child("titles").child(title_id).remove()
        return True, "تم حذف العنوان"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def release_title(title_id):
    """تحرير عنوان (جعله غير محجوز)"""
    try:
        db.child("titles").child(title_id).update({"is_taken": False})
        return True
    except:
        return False

# ============================================================
# دوال المشرفين (Supervisors)
# ============================================================
def get_supervisors(available_only=True):
    """جلب المشرفين"""
    try:
        sups = db.child("supervisors").get()
        result = []
        if sups.each():
            for s in sups.each():
                data = s.val()
                current = data.get("current_count", 0)
                max_students = data.get("max_students", 3)
                if available_only and current >= max_students:
                    continue
                result.append({
                    "id": s.key(),
                    "name": data.get("name", ""),
                    "max_students": max_students,
                    "current_count": current,
                    "is_suggested": data.get("is_suggested", False)
                })
        return result
    except Exception as e:
        st.error(f"خطأ في جلب المشرفين: {str(e)}")
        return []

def add_supervisor(name, max_students=3):
    """إضافة مشرف جديد"""
    try:
        if not name.strip():
            return False, "يرجى إدخال اسم المشرف"
        db.child("supervisors").push({
            "name": name.strip(),
            "max_students": max_students,
            "current_count": 0,
            "is_suggested": False
        })
        return True, "تم إضافة المشرف بنجاح"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def update_supervisor_max(sup_id, new_max):
    """تحديث الحد الأقصى للمشرف"""
    try:
        db.child("supervisors").child(sup_id).update({"max_students": new_max})
        return True
    except:
        return False

def delete_supervisor(sup_id):
    """حذف مشرف"""
    try:
        sup = db.child("supervisors").child(sup_id).get()
        if sup.val() and sup.val().get("current_count", 0) > 0:
            return False, "لا يمكن حذف مشرف لديه طلاب"
        db.child("supervisors").child(sup_id).remove()
        return True, "تم حذف المشرف"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

# ============================================================
# دوال التسجيل (Registrations)
# ============================================================
def register_student(data):
    """تسجيل طالب جديد"""
    try:
        # التحقق من البريد الإلكتروني
        email = data.get("student1_email")
        existing = get_registration_by_email(email)
        if existing:
            return False, "هذا البريد الإلكتروني مسجل بالفعل"
        
        # معالجة العنوان
        title_id = data.get("title_id")
        custom_title = data.get("custom_title", "")
        
        if title_id:
            # حجز العنوان
            db.child("titles").child(title_id).update({"is_taken": True})
        elif custom_title:
            # إضافة عنوان مقترح
            spec_id = data.get("specialization_id")
            ok, _ = add_title(custom_title, spec_id, is_suggested=True)
            if ok:
                titles = db.child("titles").order_by_child("name").equal_to(custom_title).get()
                if titles.each():
                    title_id = titles.each()[0].key()
                    db.child("titles").child(title_id).update({"is_taken": True})
        
        # معالجة المشرف
        sup_id = data.get("supervisor_id")
        custom_sup = data.get("custom_supervisor", "")
        
        if sup_id:
            # زيادة عدد طلاب المشرف
            sup = db.child("supervisors").child(sup_id).get()
            current = sup.val().get("current_count", 0) if sup.val() else 0
            db.child("supervisors").child(sup_id).update({"current_count": current + 1})
        elif custom_sup:
            # إضافة مشرف مقترح
            db.child("supervisors").push({
                "name": custom_sup,
                "max_students": 1,
                "current_count": 1,
                "is_suggested": True
            })
            # جلب ID المشرف الجديد
            sups = db.child("supervisors").order_by_child("name").equal_to(custom_sup).get()
            if sups.each():
                sup_id = sups.each()[0].key()
        
        # إنشاء سجل التسجيل
        registration = {
            "student1_first": data.get("student1_first", ""),
            "student1_last": data.get("student1_last", ""),
            "student1_email": data.get("student1_email", ""),
            "student2_first": data.get("student2_first", ""),
            "student2_last": data.get("student2_last", ""),
            "student2_email": data.get("student2_email", ""),
            "is_solo": data.get("is_solo", True),
            "specialization_id": data.get("specialization_id", ""),
            "title_id": title_id or "",
            "custom_title": custom_title,
            "supervisor_id": sup_id or "",
            "custom_supervisor": custom_sup,
            "notes": data.get("notes", ""),
            "change_request": None,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        db.child("registrations").push(registration)
        return True, "تم تسجيل الطالب بنجاح"
        
    except Exception as e:
        return False, f"خطأ في التسجيل: {str(e)}"

def get_registration_by_email(email):
    """البحث عن تسجيل بالبريد الإلكتروني"""
    try:
        regs = db.child("registrations").order_by_child("student1_email").equal_to(email).get()
        if regs.each():
            data = regs.each()[0].val()
            data["id"] = regs.each()[0].key()
            # إضافة معلومات إضافية
            data["spec_name"] = get_spec_name(data.get("specialization_id", ""))
            data["title_name"] = get_title_name(data.get("title_id", ""))
            data["supervisor_name"] = get_supervisor_name(data.get("supervisor_id", ""))
            return data
        return None
    except:
        return None

def get_all_registrations():
    """جلب جميع التسجيلات"""
    try:
        regs = db.child("registrations").get()
        result = []
        if regs.each():
            for r in regs.each():
                data = r.val()
                data["id"] = r.key()
                # إضافة معلومات إضافية
                data["spec_name"] = get_spec_name(data.get("specialization_id", ""))
                data["title_name"] = get_title_name(data.get("title_id", ""))
                data["supervisor_name"] = get_supervisor_name(data.get("supervisor_id", ""))
                result.append(data)
        return result
    except Exception as e:
        st.error(f"خطأ في جلب التسجيلات: {str(e)}")
        return []

def delete_registration(reg_id):
    """حذف تسجيل وإعادة إتاحة العنوان والمشرف"""
    try:
        reg = db.child("registrations").child(reg_id).get()
        if not reg.val():
            return False, "التسجيل غير موجود"
        
        data = reg.val()
        
        # تحرير العنوان
        title_id = data.get("title_id")
        if title_id:
            db.child("titles").child(title_id).update({"is_taken": False})
        
        # تقليل عدد طلاب المشرف
        sup_id = data.get("supervisor_id")
        if sup_id:
            sup = db.child("supervisors").child(sup_id).get()
            if sup.val():
                current = sup.val().get("current_count", 0)
                db.child("supervisors").child(sup_id).update({"current_count": max(0, current - 1)})
        
        # حذف التسجيل
        db.child("registrations").child(reg_id).remove()
        return True, "تم حذف التسجيل وتحرير العنوان والمشرف"
    except Exception as e:
        return False, f"خطأ: {str(e)}"

def submit_change_request(email, request_text):
    """تقديم طلب تغيير"""
    try:
        reg = db.child("registrations").order_by_child("student1_email").equal_to(email).get()
        if reg.each():
            reg_id = reg.each()[0].key()
            db.child("registrations").child(reg_id).update({"change_request": request_text})
            return True
        return False
    except:
        return False

# ============================================================
# دوال إحصائيات
# ============================================================
def get_stats():
    """جلب الإحصائيات"""
    try:
        regs = get_all_registrations()
        total = len(regs)
        solo = sum(1 for r in regs if r.get("is_solo", False))
        duo = total - solo
        
        # عدد طلبات التغيير
        changes = sum(1 for r in regs if r.get("change_request"))
        
        # حساب المتبقي للفردي (بافتراض حد أقصى 15)
        solo_remaining = max(0, 15 - solo)
        
        return {
            "total": total,
            "solo": solo,
            "duo": duo,
            "solo_remaining": solo_remaining,
            "change_requests": changes
        }
    except:
        return {"total": 0, "solo": 0, "duo": 0, "solo_remaining": 15, "change_requests": 0}

def solo_count():
    """عدد التسجيلات الفردية"""
    try:
        regs = db.child("registrations").get()
        if regs.each():
            return sum(1 for r in regs.each() if r.val().get("is_solo", False))
        return 0
    except:
        return 0

# ============================================================
# دوال مساعدة
# ============================================================
def get_spec_name(spec_id):
    """جلب اسم التخصص من ID"""
    try:
        spec = db.child("specializations").child(spec_id).get()
        if spec.val():
            return spec.val().get("name", "")
        return ""
    except:
        return ""

def get_title_name(title_id):
    """جلب اسم العنوان من ID"""
    try:
        title = db.child("titles").child(title_id).get()
        if title.val():
            return title.val().get("name", "")
        return ""
    except:
        return ""

def get_supervisor_name(sup_id):
    """جلب اسم المشرف من ID"""
    try:
        sup = db.child("supervisors").child(sup_id).get()
        if sup.val():
            return sup.val().get("name", "")
        return ""
    except:
        return ""

def get_conn():
    """للتوافق مع الكود القديم - يُرجع None"""
    return None

def init_db():
    """تهيئة قاعدة البيانات - لا حاجة مع Firebase"""
    # إضافة بيانات افتراضية إذا كانت فارغة
    try:
        if not db.child("specializations").get().each():
            defaults = ["علم الحاسوب", "الرياضيات", "الفيزياء", "الكيمياء"]
            for name in defaults:
                db.child("specializations").push({"name": name})
    except:
        pass
    return True