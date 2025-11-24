import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime

# --- 1. Студенттер тізімі (Сіз берген) ---
# Мен сіздің тізіміңізді тазалап, реттедім
STUDENT_LIST = [
    "Студентті таңдаңыз...",
    "Ардабек Ерлан",
    "Құрманбай Рамазан",
    "Қабиден Йусуф",
    "Алпысбаев Саят",
    "Асқархан Алихан",
    "Әділхан Ахметжан",
    "Орнбеков Батыржан",
    "Айкимбай Джалил",
    "Тілеубек Нұрислам",
    "Бахриден Жанат",
    "Сарсенбай Ахмет"
]

# --- 2. Пәндер тізімі (Өзіңіз өзгерте аласыз) ---
# Сіз "расписия" (кесте) туралы айттыңыз, сол үшін пәндер тізімін қостым
SUBJECT_LIST = [
    "Биология",
    "Физика",
    "Ағылшын тілі",
    "Химия",
    "Қазақстан тарихы",
    "Математика",
    "География",
    "Дүниежүзі тарихы",
    "Информатика",
    "Қазақ тілі",
    "Қазақ әдебиеті",
    "Дене шынықтыру",
    "АӘД (НВП)",
    "Басқа пән (төменге жазыңыз)"
]

# --- Google Sheets-пен жұмыс (бұл функциялар өзгеріссіз қалады) ---

@st.cache_resource
def connect_to_gsheet():
    """
    st.secrets арқылы Google Sheets-ке қосылады.
    """
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict)
        scoped_creds = creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(scoped_creds)
        return client
    except Exception as e:
        st.error(f"Google Sheets-ке қосылу кезінде қате: {e}")
        return None

def save_to_gsheet(client, sheet_name, data_row):
    """
    Берілген Google Sheet-ке жаңа қатар қосады.
    """
    try:
        sheet = client.open(sheet_name).sheet1
        # Жаңа қатарды қосу
        sheet.append_row(data_row, value_input_option='USER_ENTERED')
        return True
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"'{sheet_name}' атты Google Sheet парағы табылмады. Атын тексеріңіз.")
        return False
    except Exception as e:
        st.error(f"Деректерді сақтау кезінде қате: {e}")
        return False

# --- Streamlit интерфейсі (ТОЛЫҒЫМЕН ЖАҢАРТЫЛДЫ) ---

st.title("📚 Күнделікті баға журналы (БҚ2503)")
st.write("Студенттің күнделікті бағасын енгізіп, Google Sheets-ке сақтаңыз.")
st.divider()

with st.form("grade_form"):
    
    st.subheader("1. Баға ақпараты")
    
    # Күнді таңдау
    col1, col2 = st.columns(2)
    with col1:
        selected_day = st.date_input(
            "Сабақ күнін таңдаңыз", 
            datetime.date.today(),
            format="DD.MM.YYYY"  # <-- Осы қатарды қосыңыз
        )
    
    # Пәнді таңдау
    with col2:
        selected_subject = st.selectbox(
            "Пәнді таңдаңыз", 
            options=SUBJECT_LIST,
            index=0
        )
    
    # Егер "Басқа пән" таңдалса, жаңа өріс шығады
    other_subject = ""
    if selected_subject == "Басқа пән (төменге жазыңыз)":
        other_subject = st.text_input("Пәннің атын жазыңыз:", placeholder="Мыс: Дене шынықтыру")
        
    # Студентті таңдау
    selected_student = st.selectbox(
        "Студенттің аты-жөні", 
        options=STUDENT_LIST,
        index=0
    )
    
    st.divider()
    st.subheader("2. Баға (100-дік шкала)")
    
    # Бағаны енгізу
    grade = st.number_input(
        "Баға (0-100)", 
        min_value=0.0, 
        max_value=100.0, 
        value=75.0,  # Бастапқы мән
        step=1.0
    )
    
    # Түсініктеме
    comment = st.text_area(
        "Түсініктеме (міндетті емес)", 
        placeholder="Мысалы: Үй жұмысы №3, CӨЖ-1, Сабақтағы белсенділік..."
    )
    
    st.divider()
    
    # Батырма
    submitted = st.form_submit_button("💾 Бағаны сақтау", type="primary")

# --- Сақтау логикасы ---
if submitted:
    
    # Қай пәнді сақтау керегін анықтау
    final_subject = other_subject if selected_subject == "Басқа пән (төменге жазыңыз)" else selected_subject
    
    # Тексеру
    if final_subject == "Пәнді таңдаңыз..." or not final_subject:
        st.warning("⚠️ 'Пәнді' таңдаңыз немесе жазыңыз.")
    elif selected_student == "Студентті таңдаңыз...":
        st.warning("⚠️ 'Студентті' таңдаңыз.")
    else:
        # Бәрі дұрыс, сақтауға дайындау
        with st.spinner(f"'{selected_student}' үшін баға сақталуда..."):
            client = connect_to_gsheet()
            
            if client:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Google Sheets-тегі ЖАҢА бағандарға сәйкес деректер
                data_to_save = [
                    selected_day.strftime("%Y-%m-%d"), # A бағаны (Күні)
                    final_subject,                  # B бағаны (Пән)
                    selected_student,               # C бағаны (Студент Аты)
                    grade,                          # D бағаны (Баға)
                    comment,                        # E бағаны (Түсініктеме)
                    current_time                    # F бағаны (Енгізілген уақыт)
                ]
                
                # Google Sheet парағыңыздың аты (өзгерген жоқ)
                GOOGLE_SHEET_NAME = "Студенттердің бағалары" 
                
                if save_to_gsheet(client, GOOGLE_SHEET_NAME, data_to_save):
                    st.success(f"✅ {selected_day} күнгі '{final_subject}' пәнінен '{selected_student}' үшін баға ({grade}) сәтті сақталды!")
                    st.balloons()
                else:
                    st.warning("Нәтижелерді сақтау кезінде қате орын алды.")
