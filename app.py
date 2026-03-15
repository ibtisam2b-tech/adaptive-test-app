import streamlit as st
import pandas as pd
import random

# 1. إعدادات الصفحة
st.set_page_config(page_title="الاختبار التكيفي النهائي", layout="centered")
st.markdown("""<style>.stApp {text-align: right; direction: rtl;}</style>""", unsafe_allow_html=True)

# 2. الرابط المباشر (تأكد من وضع رابطك المعدل بـ export?format=csv)
CSV_URL = "https://docs.google.com/spreadsheets/d/1-66zj3hjoWeXhrNUk-gPhZjC3mWHDDemSzcwtb7fqyQ/export?format=csv"

@st.cache_data(ttl=1) # تقليل مدة الكاش لأقل درجة لضمان تحديث البيانات
def load_data(url):
    try:
        data = pd.read_csv(url)
        # تنظيف الأعمدة
        for col in data.columns:
            data[col] = data[col].astype(str).str.strip()
        return data
    except Exception as e:
        st.error(f"خطأ في التحميل: {e}")
        return pd.DataFrame()

# 3. تهيئة الجلسة
if 'used_indices' not in st.session_state:
    st.session_state.used_indices = []
    st.session_state.level = 2
    st.session_state.score = 0
    st.session_state.q_count = 0
    st.session_state.finished = False

st.title("🎯 الاختبار التكيفي الذكي")

df = load_data(CSV_URL)

if not df.empty:
    TOTAL_Q = 10 

    if not st.session_state.finished and st.session_state.q_count < TOTAL_Q:
        # تصفية الأسئلة: استبعاد كل ما تم حله سابقاً (منع التكرار القاطع)
        available_df = df[~df.index.isin(st.session_state.used_indices)]
        
        # محاولة اختيار سؤال من المستوى الحالي
        current_pool = available_df[available_df['level'].astype(str) == str(st.session_state.level)]
        
        # إذا فرغ المستوى، اختر من أي مستوى متاح آخر
        if current_pool.empty:
            current_pool = available_df

        if not current_pool.empty:
            # اختيار سؤال عشوائي وتخزين مكانه
            q_row = current_pool.sample(n=1).iloc[0]
            idx = q_row.name # رقم السطر الحقيقي في الجدول

            st.write(f"**السؤال {st.session_state.q_count + 1} من {TOTAL_Q}**")
            st.info(q_row['question'])

            options = [q_row['option1'], q_row['option2'], q_row['option3'], q_row['option4'] ]
            
            with st.form(key=f"form_{st.session_state.q_count}"):
                ans = st.radio("اختر الإجابة:", options)
                submit = st.form_submit_button("إرسال")

            if submit:
                # 1. منع التكرار: إضافة رقم السطر للذاكرة فوراً
                st.session_state.used_indices.append(idx)
                
                # 2. التحقق من الإجابة (تنظيف شامل للمسافات والهمزات)
                def clean(text):
                    t = str(text).strip().replace("أ","ا").replace("إ","ا").replace("آ","ا").replace("ة","ه")
                    return t

                if clean(ans) == clean(q_row['answer']):
                    st.success("إجابة صحيحة")
                    st.session_state.score += 1
                    if st.session_state.level < 3: st.session_state.level += 1
                else:
                    st.error(f"إجابة خاطئة. الصحيح: {q_row['answer']}")
                    if st.session_state.level > 1: st.session_state.level -= 1
                
                st.session_state.q_count += 1
                st.rerun()
        else:
            st.session_state.finished = True
            st.rerun()
    else:
        st.balloons()
        st.success(f"انتهى الاختبار! درجتك: {st.session_state.score} من {st.session_state.q_count}")
        if st.button("إعادة الاختبار"):
            st.session_state.clear()
            st.rerun()
