import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة والواجهة
st.set_page_config(page_title="نظام الاختبار التكيفي", layout="centered")
st.markdown("""<style>.stApp {text-align: right; direction: rtl;}</style>""", unsafe_allow_html=True)

# 2. الرابط المباشر لجدول البيانات
CSV_URL = "https://docs.google.com/spreadsheets/d/1-66zj3hjoWeXhrNUk-gPhZjC3mWHDDemSzcwtb7fqyQ/export?format=csv"

@st.cache_data(ttl=5) # تحديث البيانات كل 5 ثوانٍ لضمان عدم التعليق
def get_data(url):
    try:
        data = pd.read_csv(url)
        # تنظيف أولي للبيانات
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip()
        return data
    except Exception as e:
        st.error(f"عذراً، فشل تحميل البيانات: {e}")
        return pd.DataFrame()

# 3. دالة تنظيف النصوص العربية للمقارنة العادلة
def normalize_text(text):
    text = str(text).strip()
    replacements = {"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "  ": " "}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# 4. تهيئة متغيرات الجلسة (Session State)
if 'used_indices' not in st.session_state:
    st.session_state.used_indices = []
    st.session_state.current_level = 2
    st.session_state.total_score = 0
    st.session_state.current_step = 0
    st.session_state.is_done = False

st.title("🎯 الاختبار التكيفي الذكي")
all_data = get_data(CSV_URL)

if not all_data.empty:
    MAX_QUESTIONS = 10 

    if not st.session_state.is_done and st.session_state.current_step < MAX_QUESTIONS:
        # استبعاد الأسئلة التي ظهرت سابقاً (منع التكرار)
        available_questions = all_data[~all_data.index.isin(st.session_state.used_indices)]
        
        # اختيار سؤال بناءً على المستوى الحالي
        level_str = str(st.session_state.current_level)
        pool = available_questions[available_questions['level'] == level_str]
        
        # إذا فرغ المستوى، نسحب من أي سؤال متاح
        if pool.empty:
            pool = available_questions

        if not pool.empty:
            # اختيار سؤال عشوائي
            question_row = pool.sample(n=1).iloc[0]
            row_index = question_row.name
            
            # --- إظهار مستوى الصعوبة بوضوح ---
            levels_labels = {"1": "🟢 سهل", "2": "🟡 متوسط", "3": "🔴 صعب"}
            st.subheader(f"السؤال {st.session_state.current_step + 1} من {MAX_QUESTIONS}")
            st.markdown(f"**المستوى الحالي:** {levels_labels.get(level_str, level_str)}")
            
            st.info(question_row['question'])
            
            options = [question_row['option1'], question_row['option2'], question_row['option3'], question_row['option4']]
            
            with st.form(key=f"quiz_step_{st.session_state.current_step}"):
                user_choice = st.radio("اختر الإجابة الصحيحة:", options)
                submit_btn = st.form_submit_button("تأكيد الإجابة")

            if submit_btn:
                # منع التكرار القاطع
                st.session_state.used_indices.append(row_index)
                
                # التحقق من الإجابة
                if normalize_text(user_choice) == normalize_text(question_row['answer']):
                    st.success("إجابة صحيحة! سيتم رفع المستوى.")
                    st.session_state.total_score += 1
                    if st.session_state.current_level < 3: st.session_state.current_level += 1
                else:
                    st.error(f"إجابة خاطئة. الإجابة الصحيحة هي: {question_row['answer']}")
                    if st.session_state.current_level > 1: st.session_state.current_level -= 1
                
                st.session_state.current_step += 1
                st.rerun()
        else:
            st.session_state.is_done = True
            st.rerun()
    else:
        st.balloons()
        st.header("🏁 النتيجة النهائية")
        st.metric("عدد الإجابات الصحيحة", f"{st.session_state.total_score} من {MAX_QUESTIONS}")
        if st.button("إعادة الاختبار"):
            st.session_state.clear()
            st.rerun()
