import streamlit as st
import pandas as pd

# إعدادات الواجهة واللغة العربية
st.set_page_config(page_title="الاختبار التكيفي المطور", layout="centered")
st.markdown("""
    <style>
    .stApp {text-align: right; direction: rtl;}
    div[role="radiogroup"] {direction: rtl; gap: 10px;}
    .stProgress > div > div > div > div { background-color: #4CAF50; }
    </style>
    """, unsafe_allow_html=True)

# الرابط المباشر للجدول (تأكد من وضع رابطك هنا)
CSV_URL = "https://docs.google.com/spreadsheets/d/1-66zj3hjoWeXhrNUk-gPhZjC3mWHDDemSzcwtb7fqyQ/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        data = pd.read_csv(CSV_URL)
        # تنظيف البيانات من المسافات الزائدة
        data = data.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        return data
    except Exception as e:
        st.error(f"خطأ في الاتصال بالبيانات: {e}")
        return pd.DataFrame()

# تهيئة متغيرات الجلسة
if 'level' not in st.session_state:
    st.session_state.level = 2 # البداية من المتوسط
    st.session_state.score = 0
    st.session_state.q_count = 0
    st.session_state.finished = False
    st.session_state.used_questions = [] # لقائمة الأسئلة التي حُلت

st.title("🎯 الاختبار التكيفي الذكي")
df = load_data()

if not df.empty:
    TOTAL_QUESTIONS = 10 # يمكنك تغيير عدد أسئلة الاختبار من هنا
    
    if not st.session_state.finished:
        # إظهار التقدم
        progress = st.session_state.q_count / TOTAL_QUESTIONS
        st.progress(progress)
        
        # تحديد المستوى الحالي بصرياً
        level_labels = {1: "🟢 مستوى سهل", 2: "🟡 مستوى متوسط", 3: "🔴 مستوى صعب"}
        st.sidebar.subheader("إحصائيات الاختبار")
        st.sidebar.info(f"المستوى الحالي: {level_labels[st.session_state.level]}")
        st.sidebar.write(f"الأسئلة المجابة: {st.session_state.q_count} من {TOTAL_QUESTIONS}")

        # تصفية الأسئلة: حسب المستوى + لم تُحل بعد
        current_pool = df[(df['level'] == st.session_state.level) & (~df['question'].isin(st.session_state.used_questions))]
        
        # إذا فرغ مستوى معين، نأخذ من الأقرب له
        if current_pool.empty:
            current_pool = df[~df['question'].isin(st.session_state.used_questions)]

        if not current_pool.empty:
            q_row = current_pool.sample(n=1).iloc[0]
            st.subheader(f"السؤال رقم {st.session_state.q_count + 1}")
            st.info(q_row['question'])
            
            options = [str(q_row['option1']), str(q_row['option2']), str(q_row['option3']), str(q_row['option4'])]
            
            with st.form(key=f"q_{st.session_state.q_count}"):
                choice = st.radio("اختر الإجابة الصحيحة:", options)
                submit = st.form_submit_button("إرسال الإجابة")
            
            if submit:
                # تسجيل السؤال كـ "مستعمل"
                st.session_state.used_questions.append(q_row['question'])
                
                # التحقق من الإجابة (تكييف الصعوبة)
                if str(choice).strip() == str(q_row['answer']).strip():
                    st.success("إجابة صحيحة! أحسنت.")
                    st.session_state.score += 1
                    if st.session_state.level < 3: st.session_state.level += 1
                else:
                    st.error(f"إجابة خاطئة. الإجابة الصحيحة هي: {q_row['answer']}")
                    if st.session_state.level > 1: st.session_state.level -= 1
                
                st.session_state.q_count += 1
                
                if st.session_state.q_count >= TOTAL_QUESTIONS:
                    st.session_state.finished = True
                st.rerun()
        else:
            st.warning("انتهت الأسئلة المتوفرة في الجدول!")
            st.session_state.finished = True
            
    else:
        # شاشة النتيجة النهائية
        st.balloons()
        st.header("🏁 اكتمل الاختبار")
        final_score = (st.session_state.score / TOTAL_QUESTIONS) * 100
        st.metric(label="درجتك النهائية", value=f"{final_score}%", delta=f"{st.session_state.score} إجابة صحيحة")
        
        if st.button("إعادة الاختبار من جديد"):
            st.session_state.clear()
            st.rerun()
