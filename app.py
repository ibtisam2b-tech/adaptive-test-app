import streamlit as st
import pandas as pd

# إعدادات الواجهة العربية
st.set_page_config(page_title="الاختبار التكيفي", layout="centered")
st.markdown("<style>.stApp {text-align: right; direction: rtl;}</style>", unsafe_allow_html=True)

# الرابط المباشر (ضع الرابط الذي جهزته هنا)
CSV_URL = "https://docs.google.com/spreadsheets/d/1-66zj3hjoWeXhrNUk-gPhZjC3mWHDDemSzcwtb7fqyQ/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        return pd.read_csv(CSV_URL)
    except Exception as e:
        st.error(f"خطأ في قراءة البيانات: {e}")
        return pd.DataFrame()

# تهيئة الجلسة
if 'level' not in st.session_state:
    st.session_state.level = 2
    st.session_state.score = 0
    st.session_state.q_count = 0
    st.session_state.finished = False

st.title("🎯 الاختبار التكيفي الذكي")

df = load_data()

if not df.empty:
    if not st.session_state.finished:
        # تصفية الأسئلة حسب المستوى الحالي
        current_pool = df[df['level'] == st.session_state.level]
        
        if not current_pool.empty:
            # اختيار سؤال
            q_row = current_pool.sample(n=1).iloc[0]
            st.subheader(f"السؤال {st.session_state.q_count + 1}")
            st.info(q_row['question'])
            
            options = [str(q_row['option1']), str(q_row['option2']), str(q_row['option3']), str(q_row['option4'])]
            
            with st.form(key='quiz'):
                choice = st.radio("اختر الإجابة:", options)
                submit = st.form_submit_button("إرسال")
            
            if submit:
                if str(choice).strip() == str(q_row['answer']).strip():
                    st.success("صح!")
                    st.session_state.score += 1
                    if st.session_state.level < 3: st.session_state.level += 1
                else:
                    st.error(f"خطأ! الإجابة هي: {q_row['answer']}")
                    if st.session_state.level > 1: st.session_state.level -= 1
                
                st.session_state.q_count += 1
                if st.session_state.q_count >= 5: st.session_state.finished = True
                st.rerun()
    else:
        st.balloons()
        st.header("النتيجة النهائية")
        st.write(f"درجتك: {st.session_state.score} من 5")
        if st.button("إعادة"):
            st.session_state.clear()
            st.rerun()
