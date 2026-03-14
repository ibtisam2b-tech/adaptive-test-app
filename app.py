import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة واللغة العربية
st.set_page_config(page_title="الاختبار التكيفي الذكي", layout="centered")
st.markdown("""
    <style>
    .stApp {text-align: right; direction: rtl;}
    div[role="radiogroup"] {direction: rtl; gap: 10px;}
    .stProgress > div > div > div > div { background-color: #4CAF50; }
    </style>
    """, unsafe_allow_html=True)

# 2. الرابط المباشر للجدول (تأكد من وضع رابطك هنا)
# ملاحظة: يجب أن ينتهي الرابط بـ export?format=csv
CSV_URL = "https://docs.google.com/spreadsheets/d/1-66zj3hjoWeXhrNUk-gPhZjC3mWHDDemSzcwtb7fqyQ/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    try:
        data = pd.read_csv(CSV_URL)
        # تنظيف البيانات الأساسية من المسافات في الأعمدة النصية
        for col in ['question', 'option1', 'option2', 'option3', 'option4', 'answer']:
            if col in data.columns:
                data[col] = data[col].astype(str).str.strip()
        return data
    except Exception as e:
        st.error(f"خطأ في الاتصال بالبيانات: {e}")
        return pd.DataFrame()

# 3. تهيئة متغيرات الجلسة (Session State)
if 'level' not in st.session_state:
    st.session_state.level = 2  # يبدأ المستوى من متوسط
    st.session_state.score = 0
    st.session_state.q_count = 0
    st.session_state.finished = False
    st.session_state.used_indices = [] # ذاكرة أرقام الصفوف لمنع التكرار

st.title("🎯 الاختبار التكيفي الذكي")
df = load_data()

if not df.empty:
    TOTAL_QUESTIONS = 10  # يمكنك تغيير إجمالي عدد الأسئلة من هنا
    
    if not st.session_state.finished:
        # إظهار شريط التقدم ومستوى الصعوبة
        progress = st.session_state.q_count / TOTAL_QUESTIONS
        st.progress(progress)
        
        level_labels = {1: "🟢 مستوى سهل", 2: "🟡 مستوى متوسط", 3: "🔴 مستوى صعب"}
        st.sidebar.subheader("إحصائيات الاختبار")
        st.sidebar.info(f"المستوى الحالي: {level_labels[st.session_state.level]}")
        st.sidebar.write(f"الأسئلة المجابة: {st.session_state.q_count} من {TOTAL_QUESTIONS}")

        # 4. خوارزمية اختيار السؤال (التكيف + منع التكرار)
        # نستخدم index الجدول لضمان عدم التكرار 100%
        df_with_idx = df.copy()
        df_with_idx['original_index'] = df.index
        
        # تصفية الأسئلة حسب المستوى الحالي والتي لم تُحل بعد
        current_pool = df_with_idx[
            (df_with_idx['level'] == st.session_state.level) & 
            (~df_with_idx['original_index'].isin(st.session_state.used_indices))
        ]
        
        # إذا انتهت أسئلة هذا المستوى، ابحث في أقرب مستوى آخر
        if current_pool.empty:
            current_pool = df_with_idx[~df_with_idx['original_index'].isin(st.session_state.used_indices)]

        if not current_pool.empty:
            # اختيار سؤال عشوائي من المتوفر
            q_row = current_pool.sample(n=1).iloc[0]
            current_q_idx = int(q_row['original_index'])
            
            st.subheader(f"السؤال رقم {st.session_state.q_count + 1}")
            st.info(q_row['question'])
            
            options = [str(q_row['option1']), str(q_row['option2']), str(q_row['option3']), str(q_row['option4'])]
            
            # نموذج الإجابة
            with st.form(key=f"q_form_{st.session_state.q_count}"):
                choice = st.radio("اختر الإجابة الصحيحة:", options)
                submit = st.form_submit_button("إرسال الإجابة")
            
            if submit:
                # حفظ رقم السؤال في "المستعمل" لمنع تكراره
                st.session_state.used_indices.append(current_q_idx)
                
                # التحقق من الإجابة (مقارنة ذكية خالية من المسافات)
                user_answer = str(choice).strip()
                correct_answer = str(q_row['answer']).strip()
                
                if user_answer == correct_answer:
                    st.success("✅ إجابة صحيحة!")
                    st.session_state.score += 1
                    # رفع المستوى إذا لم يكن في الحد الأقصى
                    if st.session_state.level < 3: st.session_state.level += 1
                else:
                    st.error(f"❌ إجابة خاطئة. الإجابة الصحيحة كانت: {correct_answer}")
                    # خفض المستوى إذا لم يكن في الحد الأدنى
                    if st.session_state.level > 1: st.session_state.level -= 1
                
                st.session_state.q_count += 1
                
                # التحقق من نهاية الاختبار
                if st.session_state.q_count >= TOTAL_QUESTIONS:
                    st.session_state.finished = True
                st.rerun()
        else:
            st.warning("⚠️ لا توجد أسئلة إضافية متوفرة في الجدول!")
            st.session_state.finished = True
            
    else:
        # 5. شاشة النتيجة النهائية
        st.balloons()
        st.header("🎊 اكتمل الاختبار")
        final_percentage = (st.session_state.score / TOTAL_QUESTIONS) * 100
        
        col1, col2 = st.columns(2)
        col1.metric("الدرجة النهائية", f"{final_percentage}%")
        col2.metric("الإجابات الصحيحة", f"{st.session_state.score} / {TOTAL_QUESTIONS}")

        if st.button("إعادة الاختبار من جديد"):
            st.session_state.clear()
            st.rerun()
