import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="نظام الاختبار الذكي", layout="centered")
st.markdown("<style>.stApp {text-align: right; direction: rtl;}</style>", unsafe_allow_html=True)

# 2. الرابط المباشر
CSV_URL = "https://docs.google.com/spreadsheets/d/1-66zj3hjoWeXhrNUk-gPhZjC3mWHDDemSzcwtb7fqyQ/export?format=csv"

@st.cache_data(ttl=1)
def load_data():
    try:
        data = pd.read_csv(CSV_URL)
        return data
    except Exception as e:
        st.error(f"خطأ في التحميل: {e}")
        return pd.DataFrame()

# 3. دالة تنظيف الإجابات (لحل مشكلة إجابة صحيحة وتظهر خطأ)
def check_answers(user_ans, correct_ans):
    def normalize(t):
        t = str(t).strip().lower()
        repls = {"أ": "ا", "إ": "ا", "آ": "ا", "ة": "ه", "  ": " "}
        for old, new in repls.items():
            t = t.replace(old, new)
        return t
    return normalize(user_ans) == normalize(correct_ans)

# 4. تهيئة المتغيرات (تأكد من عدم تصفيرها عند كل رن)
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.used_ids = []
    st.session_state.lvl = 2
    st.session_state.scr = 0
    st.session_state.count = 0
    st.session_state.done = False

st.title("🎯 اختبار تكيّفي دقيق")

df = load_data()

if not df.empty:
    LIMIT = 10 
    
    if not st.session_state.done and st.session_state.count < LIMIT:
        # منع التكرار: استبعاد الأسئلة المستخدمة بناءً على نص السؤال (لأن النص فريد)
        remaining = df[~df['question'].isin(st.session_state.used_ids)]
        
        # تصفية حسب المستوى
        pool = remaining[remaining['level'].astype(str) == str(st.session_state.lvl)]
        if pool.empty: pool = remaining # إذا خلص المستوى اسحب من غيره

        if not pool.empty:
            # اختيار السؤال
            q_row = pool.sample(n=1).iloc[0]
            
            # عرض المعلومات
            lvls = {"1": "🟢 سهل", "2": "🟡 متوسط", "3": "🔴 صعب"}
            st.subheader(f"سؤال {st.session_state.count + 1} من {LIMIT}")
            st.markdown(f"**المستوى:** {lvls.get(str(st.session_state.lvl))}")
            st.info(q_row['question'])
            
            opts = [str(q_row['option1']), str(q_row['option2']), str(q_row['option3']), str(q_row['option4'])]
            
            # شكل الفورم
            with st.form(key=f"q_form_{st.session_state.count}"):
                user_choice = st.radio("اختر إجابتك:", opts)
                submitted = st.form_submit_button("إرسال الإجابة")
                
                if submitted:
                    # إضافة السؤال للقائمة "فوراً" لمنع تكراره
                    st.session_state.used_ids.append(q_row['question'])
                    
                    # التحقق
                    if check_answers(user_choice, q_row['answer']):
                        st.success("✅ صح!")
                        st.session_state.scr += 1
                        if st.session_state.lvl < 3: st.session_state.lvl += 1
                    else:
                        st.error(f"❌ خطأ! الإجابة الصحيحة هي: {q_row['answer']}")
                        if st.session_state.lvl > 1: st.session_state.lvl -= 1
                    
                    st.session_state.count += 1
                    st.rerun()
        else:
            st.warning("انتهت الأسئلة!")
            st.session_state.done = True
    else:
        st.balloons()
        st.header("🏁 النتيجة")
        st.metric("درجتك", f"{st.session_state.scr} من {st.session_state.count}")
        if st.button("إعادة"):
            for key in st.session_state.keys(): del st.session_state[key]
            st.rerun()
