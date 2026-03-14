import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import plotly.express as px

# 1. إعدادات الصفحة ودعم اللغة العربية (RTL)
st.set_page_config(page_title="نظام الاختبار التكيفي", layout="centered")
st.markdown("""
    <style>
    .stApp {text-align: right; direction: rtl;}
    div[role="radiogroup"] {direction: rtl;}
    </style>
    """, unsafe_allow_html=True)

# 2. الاتصال بـ Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. دالة تحميل الأسئلة من ورقة Questions
@st.cache_data(ttl=60)
def load_questions():
    return conn.read(worksheet="Questions")

# 4. تهيئة متغيرات الجلسة (للحفاظ على تقدم الطالب)
if 'level' not in st.session_state:
    st.session_state.level = 2  # يبدأ بمستوى متوسط
    st.session_state.score = 0
    st.session_state.q_count = 0
    st.session_state.finished = False

# القائمة الجانبية للتنقل
menu = st.sidebar.selectbox("القائمة الرئيسية", ["خوض الاختبار", "لوحة تحكم المعلم"])

# --- صفحة الاختبار ---
if menu == "خوض الاختبار":
    st.title("📝 الاختبار التكيفي الذكي")
    
    df_questions = load_questions()

    if not st.session_state.finished:
        # اختيار الأسئلة بناءً على المستوى الحالي للطالب
        current_pool = df_questions[df_questions['level'] == st.session_state.level]
        
        if not current_pool.empty:
            # اختيار سؤال عشوائي من المستوى المطلوب
            question_row = current_pool.sample(n=1).iloc[0]
            
            st.write(f"### السؤال رقم: {st.session_state.q_count + 1}")
            st.info(question_row['question'])
            
            # ترتيب الخيارات
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
                # التحقق من الإجابة
                if str(user_choice).strip() == str(question_row['answer']).strip():
                    st.success("✅ إجابة صحيحة! سيتم رفع مستوى الصعوبة.")
                    st.session_state.score += 1
                    if st.session_state.level < 3: st.session_state.level += 1
                else:
                    st.error(f"❌ إجابة خاطئة. الإجابة الصحيحة كانت: {question_row['answer']}")
                    if st.session_state.level > 1: st.session_state.level -= 1
                
                st.session_state.q_count += 1
                
                # إنهاء الاختبار بعد عدد معين من الأسئلة (مثلاً 5 أسئلة)
                if st.session_state.q_count >= 5:
                    st.session_state.finished = True
                
                st.rerun()
        else:
            st.warning("لا توجد أسئلة كافية في هذا المستوى في جدول البيانات.")
    
    else:
        # شاشة النهاية
        st.balloons()
        st.header("🎊 انتهى الاختبار!")
        st.write(f"درجتك النهائية: **{st.session_state.score}** من 5")
        
        student_name = st.text_input("أدخل اسمك لحفظ النتيجة:")
        if st.button("حفظ وإرسال النتيجة"):
            if student_name:
                # كود تسجيل النتيجة في ورقة Results
                new_data = pd.DataFrame([{
                    "Name": student_name,
                    "Score": st.session_state.score,
                    "Level": st.session_state.level,
                    "Time": pd.Timestamp.now()
                }])
                existing_res = conn.read(worksheet="Results")
                updated_res = pd.concat([existing_res, new_data], ignore_index=True)
                conn.update(worksheet="Results", data=updated_res)
                st.success("تم تسجيل نتيجتك في السجل بنجاح!")
            else:
                st.warning("يرجى كتابة اسمك أولاً.")
        
        if st.button("إعادة الاختبار"):
            st.session_state.level = 2
            st.session_state.score = 0
            st.session_state.q_count = 0
            st.session_state.finished = False
            st.rerun()

# --- صفحة المعلم ---
elif menu == "لوحة تحكم المعلم":
    st.title("📊 لوحة تحكم المعلم")
    password = st.sidebar.text_input("كلمة مرور الإدارة", type="password")
    
    if password == "1234":
        df_results = conn.read(worksheet="Results")
        if not df_results.empty:
            st.subheader("نتائج الطلاب الأخيرة")
            st.dataframe(df_results)
            
            # رسم بياني للنتائج
            fig = px.bar(df_results, x="Name", y="Score", color="Score", title="توزيع درجات الطلاب")
            st.plotly_chart(fig)
        else:
            st.info("لا توجد نتائج مسجلة بعد.")
    else:
        st.warning("يرجى إدخال كلمة المرور الصحيحة لمشاهدة البيانات.")
