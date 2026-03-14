import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة ودعم اللغة العربية (RTL)
st.set_page_config(page_title="نظام الاختبار التكيفي", layout="centered")
st.markdown("""
    <style>
    .stApp {text-align: right; direction: rtl;}
    div[role="radiogroup"] {direction: rtl;}
    </style>
    """, unsafe_allow_html=True)

# 2. دالة تحميل الأسئلة (طريقة الرابط المباشر لتجنب الأخطاء)
@st.cache_data(ttl=60)
def load_questions():
    try:
        # جلب الرابط من Secrets
        raw_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # تحويل الرابط لصيغة تصدير CSV مباشرة
        csv_url = raw_url.replace("/edit?usp=sharing", "/export?format=csv&gid=0")
        return pd.read_csv(csv_url)
    except Exception as e:
        st.error(f"فشل الاتصال بجدول البيانات: {e}")
        return pd.DataFrame()

# 3. تهيئة متغيرات الجلسة
if 'level' not in st.session_state:
    st.session_state.level = 2
    st.session_state.score = 0
    st.session_state.q_count = 0
    st.session_state.finished = False

# القائمة الجانبية
menu = st.sidebar.selectbox("القائمة الرئيسية", ["خوض الاختبار", "لوحة تحكم المعلم"])

if menu == "خوض الاختبار":
    st.title("📝 الاختبار التكيفي الذكي")
    
    df_questions = load_questions()

    if not df_questions.empty:
        if not st.session_state.finished:
            # تصفية الأسئلة حسب المستوى
            current_pool = df_questions[df_questions['level'] == st.session_state.level]
            
            if not current_pool.empty:
                question_row = current_pool.sample(n=1).iloc[0]
                
                st.write(f"### السؤال رقم: {st.session_state.q_count + 1}")
                st.info(question_row['question'])
                
                options = [
                    str(question_row['option1']), 
                    str(question_row['option2']), 
                    str(question_row['option3']), 
                    str(question_row['option4'])
                ]
                
                with st.form(key='quiz_form'):
                    user_choice = st.radio("اختر الإجابة الصحيحة:", options)
                    submit = st.form_submit_button("إرسال الإجابة")

                if submit:
                    if str(user_choice).strip() == str(question_row['answer']).strip():
                        st.success("✅ إجابة صحيحة!")
                        st.session_state.score += 1
                        if st.session_state.level < 3: st.session_state.level += 1
                    else:
                        st.error(f"❌ إجابة خاطئة. الإجابة هي: {question_row['answer']}")
                        if st.session_state.level > 1: st.session_state.level -= 1
                    
                    st.session_state.q_count += 1
                    if st.session_state.q_count >= 5: # عدد الأسئلة
                        st.session_state.finished = True
                    st.rerun()
            else:
                st.warning("لا توجد أسئلة كافية لهذا المستوى.")
        else:
            st.balloons()
            st.header("🎊 انتهى الاختبار!")
            st.write(f"درجتك النهائية: **{st.session_state.score}** من 5")
            if st.button("إعادة الاختبار"):
                st.session_state.clear()
                st.rerun()

elif menu == "لوحة تحكم المعلم":
    st.title("📊 لوحة تحكم المعلم")
    pwd = st.sidebar.text_input("كلمة المرور", type="password")
    if pwd == "1234":
        st.write("هنا تظهر نتائج الطلاب عند ربط ورقة النتائج (Results).")
    else:
        st.warning("أدخل كلمة المرور الصحيحة.")
