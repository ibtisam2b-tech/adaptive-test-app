import streamlit as st
import pandas as pd
import random

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام الاختبار الذكي", layout="centered")
st.markdown("<style>.stApp {text-align: right; direction: rtl;}</style>", unsafe_allow_html=True)

# 2. الرابط المباشر - تأكد من وضع رابط CSV الصحيح هنا
CSV_URL = "https://docs.google.com/spreadsheets/d/1-66zj3hjoWeXhrNUk-gPhZjC3mWHDDemSzcwtb7fqyQ/export?format=csv"

@st.cache_data(ttl=60) # تحديث كل دقيقة بدلاً من ثانية واحدة لتقليل الضغط
def load_data():
    try:
        # قراءة البيانات مع التأكد من أن جميع الأعمدة نصوص لتجنب مشاكل المقارنة
        data = pd.read_csv(CSV_URL, dtype=str)
        # تنظيف أسماء الأعمدة من أي مسافات زائدة
        data.columns = [c.strip() for c in data.columns]
        return data
    except Exception as e:
        st.error(f"خطأ في تحميل البيانات: {e}")
        return pd.DataFrame()

# 3. دالة تنظيف ومقارنة الإجابات المتقدمة
def check_answers(user_ans, correct_ans):
    if pd.isna(user_ans) or pd.isna(correct_ans):
        return False
    
    def normalize(t):
        t = str(t).strip().lower()
        # توحيد الحروف العربية المتشابهة
        repls = {
            "أ": "ا", "إ": "ا", "آ": "ا", 
            "ة": "ه", 
            "ى": "ي",
            "  ": " " # تقليل المسافات المزدوجة
        }
        for old, new in repls.items():
            t = t.replace(old, new)
        return t.strip()
    
    return normalize(user_ans) == normalize(correct_ans)

# 4. تهيئة متغيرات الحالة (Session State)
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.used_ids = [] # قائمة بالأسئلة التي تمت الإجابة عليها
    st.session_state.lvl = 2       # المستوى الحالي (1: سهل، 2: متوسط، 3: صعب)
    st.session_state.scr = 0       # النتيجة
    st.session_state.count = 0     # عدد الأسئلة المجابة
    st.session_state.done = False  # هل انتهى الاختبار؟
    st.session_state.current_q = None # السؤال الحالي (لمنع التكرار العشوائي)

st.title("🎯 اختبار تكيّفي ذكي")

df = load_data()

if not df.empty:
    LIMIT = 10 
    
    # التحقق من انتهاء الاختبار
    if st.session_state.count >= LIMIT:
        st.session_state.done = True

    if not st.session_state.done:
        # إذا لم يكن هناك سؤال حالي، قم باختيار واحد
        if st.session_state.current_q is None:
            # استبعاد الأسئلة المستخدمة
            remaining = df[~df['question'].isin(st.session_state.used_ids)]
            
            if remaining.empty:
                st.warning("انتهت جميع الأسئلة المتوفرة في قاعدة البيانات!")
                st.session_state.done = True
                st.rerun()
            
            # تصفية حسب المستوى الحالي
            pool = remaining[remaining['level'].astype(str) == str(st.session_state.lvl)]
            
            # إذا كان مستوى معين فارغاً، نسحب من أقرب مستوى متاح
            if pool.empty:
                pool = remaining
            
            # اختيار سؤال عشوائي وتخزينه في الحالة
            st.session_state.current_q = pool.sample(n=1).iloc[0].to_dict()

        # عرض السؤال الحالي من الحالة
        q_row = st.session_state.current_q
        lvls = {"1": "🟢 سهل", "2": "🟡 متوسط", "3": "🔴 صعب"}
        
        st.subheader(f"السؤال {st.session_state.count + 1} من {LIMIT}")
        st.markdown(f"**المستوى الحالي:** {lvls.get(str(st.session_state.lvl), st.session_state.lvl)}")
        
        # صندوق السؤال
        st.info(q_row['question'])
        
        # تجهيز الخيارات وتنظيفها
        opts = [str(q_row[f'option{i}']).strip() for i in range(1, 5) if f'option{i}' in q_row and pd.notna(q_row[f'option{i}'])]
        
        # استخدام نموذج (Form) للإجابة
        with st.form(key=f"q_form_{st.session_state.count}"):
            user_choice = st.radio("اختر الإجابة الصحيحة:", opts)
            submitted = st.form_submit_button("إرسال الإجابة")
            
            if submitted:
                # 1. التحقق من الإجابة
                is_correct = check_answers(user_choice, q_row['answer'])
                
                # 2. تحديث الحالة
                st.session_state.used_ids.append(q_row['question'])
                st.session_state.count += 1
                
                if is_correct:
                    st.success("✅ إجابة صحيحة!")
                    st.session_state.scr += 1
                    # رفع المستوى إذا كانت الإجابة صحيحة (بحد أقصى 3)
                    if st.session_state.lvl < 3:
                        st.session_state.lvl += 1
                else:
                    st.error(f"❌ إجابة خاطئة! الإجابة الصحيحة هي: {q_row['answer']}")
                    # خفض المستوى إذا كانت الإجابة خاطئة (بحد أدنى 1)
                    if st.session_state.lvl > 1:
                        st.session_state.lvl -= 1
                
                # 3. مسح السؤال الحالي ليتم اختيار واحد جديد في الرنة القادمة
                st.session_state.current_q = None
                
                # إظهار رسالة قصيرة قبل الانتقال
                st.info("جاري تحميل السؤال التالي...")
                st.rerun()

    else:
        # عرض النتائج النهائية
        st.balloons()
        st.header("🏁 انتهى الاختبار!")
        
        col1, col2 = st.columns(2)
        col1.metric("درجتك النهائية", f"{st.session_state.scr} من {st.session_state.count}")
        
        percentage = (st.session_state.scr / st.session_state.count) * 100 if st.session_state.count > 0 else 0
        col2.metric("النسبة المئوية", f"{percentage:.1f}%")
        
        if percentage >= 50:
            st.success("أحسنت! أداء جيد.")
        else:
            st.warning("تحتاج إلى مزيد من الممارسة.")
            
        if st.button("إعادة الاختبار من جديد"):
            # مسح الحالة لإعادة البدء
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
else:
    st.error("لم يتم العثور على بيانات. يرجى التأكد من رابط ملف CSV.")
