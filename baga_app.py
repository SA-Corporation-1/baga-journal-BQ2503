import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import pandas as pd # Аналитика үшін қосылды
from streamlit_option_menu import option_menu
import streamlit_antd_components as sac # Жаңа дизайн кітапханасы

# --- 0. Парақ баптаулары (Беттің аты мен иконкасы) ---
st.set_page_config(
    page_title="БҚ2503 Журналы",
    page_icon="📚",
    layout="wide"
)

# --- 1. Студенттер тізімі (Өзгермейді) ---
STUDENT_LIST = [
    "Студентті таңдаңыз...",
    "Ардабек Ерлан", "Құрманбай Рамазан", "Қабиден Йусуф",
    "Алпысбаев Саят", "Асқархан Алихан", "Әділхан Ахметжан",
    "Орнбеков Батыржан", "Айкимбай Джалил", "Тілеубек Нұрислам",
    "Бахриден Жанат", "Сарсенбай Ахмет"
]

# --- 2. Пәндер кестесі (Өзгермейді) ---
DAILY_SCHEDULE = {
    0: ["Қазақ тілі (онлайн)", "Физика", "Ағылшын тілі", "Орыс тілі және әдебиеті (онлайн)", "Химия (онлайн)"], # Дс
    1: ["Биология", "Информатика", "Математика"], # Сс
    2: ["Математика", "Қазақ әдебиеті", "Қазақ тілі (онлайн)"], # Ср
    3: ["Дене тәрбиесі", "Химия", "Қазақстан тарихы"], # Бс
    4: ["Орыс тілі және әдебиеті", "Алғашқы әскери және технологиялық дайындық"], # Жм
    5: [], # Сн
    6: []  # Жк
}

# --- 3. Google Sheets функциялары ---

# Қосылу функциясы (өзгеріссіз)
@st.cache_resource
def connect_to_gsheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict)
        scoped_creds = creds.with_scopes([
            "https.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(scoped_creds)
        return client
    except Exception as e:
        st.error(f"Google Sheets-ке қосылу кезінде қате: {e}")
        return None

# Сақтау функциясы (өзгеріссіз)
def save_to_gsheet(client, sheet_name, data_row):
    try:
        sheet = client.open(sheet_name).sheet1
        sheet.append_row(data_row, value_input_option='USER_ENTERED')
        return True
    except Exception as e:
        st.error(f"Деректерді сақтау кезінде қате: {e}")
        return False

# ЖАҢА ФУНКЦИЯ (Аналитика үшін деректерді оқу)
# UnhashableTypeError қатесін түзету: 'client' аргументі алынып тасталды
@st.cache_data(ttl=600) # Деректерді 10 минут сақтау
def load_data_from_gsheet(sheet_name):
    try:
        # connect_to_gsheet() функциясы осы жерде шақырылады
        client = connect_to_gsheet()
        if client is None:
             return pd.DataFrame() # Егер қосыла алмаса, бос DataFrame қайтару

        sheet = client.open(sheet_name).sheet1
        values = sheet.get_all_values()
        if not values or len(values) < 2:
            return pd.DataFrame() # Егер бос болса, бос DataFrame қайтару
        
        # Google Sheet-тегі баған аттары
        headers = ["Күні", "Пән", "Студент Аты", "Баға", "Түсініктеме", "Енгізілген уақыт"]
        
        # Деректерді DataFrame-ге айналдыру (1-қатарды баған ретінде алу)
        df = pd.DataFrame(values[1:], columns=headers)
        
        # Баға бағанын санға айналдыру (қателерді елемеу)
        df['Баға'] = pd.to_numeric(df['Баға'], errors='coerce')
        
        # Күні бағанын дата форматына айналдыру
        df['Күні'] = pd.to_datetime(df['Күні'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Деректерді оқу кезінде қате: {e}")
        return pd.DataFrame()

# --- 4. Streamlit интерфейсі (ЖАҢАРТЫЛҒАН) ---

st.title("📚 БҚ2503 Журналы: Бақылау тақтасы")

# Кәсіби навигация мәзірі (ЖАҢАРТЫЛДЫ - Аналитика қосылды)
selected_tab = option_menu(
    menu_title=None, 
    options=["📊 Аналитика", "📝 Баға енгізу", "🗓️ Сабақ кестесі", "🔔 Хабарландырулар"], 
    icons=['bar-chart-line-fill', 'pencil-square', 'calendar-week', 'bell-fill'], 
    menu_icon="cast", 
    default_index=0, 
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#0E1117"},
        "icon": {"color": "#FF4B4B", "font-size": "18px"}, 
        "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#262730"},
        "nav-link-selected": {"background-color": "#FF4B4B", "color": "white", "font-weight": "bold"},
    }
)

GOOGLE_SHEET_NAME = "Студенттердің бағалары" # Google Sheet аты

# --- БӨЛІМ 1: АНАЛИТИКА (ЖАҢА БӨЛІМ) ---
if selected_tab == "📊 Аналитика":
    st.subheader("📊 Жалпы үлгерім аналитикасы")
    
    # UnhashableTypeError қатесін түзету: 'client' аргументі алынып тасталды
    df = load_data_from_gsheet(GOOGLE_SHEET_NAME)
        
    # IndentationError қатесін түзету: Бұл жол дұрыс шегіністе тұр
    if df.empty:
        st.warning("📊 Аналитика үшін әлі деректер жоқ. Бірнеше баға енгізіңіз.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("📝 Барлық баға саны", f"{df.shape[0]} дана")
        col2.metric("💯 Орташа баға", f"{df['Баға'].mean():.1f} / 100")
        col3.metric("🧑‍🎓 Студент саны", f"{df['Студент Аты'].nunique()} адам")
        
        st.divider()
        
        # График 1: Студенттер бойынша орташа баға
        st.subheader("Студенттердің орташа бағасы")
        # .dropna() қосылды, егер бағаны оқи алмаса қате кетпеу үшін
        avg_grades = df.dropna(subset=['Баға']).groupby('Студент Аты')['Баға'].mean().reset_index().sort_values(by="Баға", ascending=False)
        st.bar_chart(avg_grades, x="Студент Аты", y="Баға")
        
        # График 2: Соңғы енгізілген бағалар
        st.subheader("Соңғы енгізілген 10 баға")
        st.dataframe(
            df.tail(10)[["Күні", "Пән", "Студент Аты", "Баға"]], 
            use_container_width=True,
            hide_index=True
        )

# --- БӨЛІМ 2: БАҒА ЕНГІЗУ (ДИЗАЙН ЖАҢАРТЫЛДЫ) ---
if selected_tab == "📝 Баға енгізу":
    
    # 1. КАРТОЧКА: Сабақ ақпараты (Формадан тыс)
    with sac.card(title="1. Сабақ ақпараты", icon="calendar-event", collapsible=True, color='red'):
        col1, col2 = st.columns(2)
        with col1:
            selected_day = st.date_input(
                "📅 Сабақ күнін таңдаңыз", 
                datetime.date.today(),
                format="DD.MM.YYYY"
            )
        
        with col2:
            day_of_week = selected_day.weekday() 
            week_number = selected_day.isocalendar()[1] 
            is_even_week = (week_number % 2 == 0)
            todays_subjects = list(DAILY_SCHEDULE.get(day_of_week, []))

            if day_of_week == 2:
                if is_even_week: todays_subjects.insert(1, "Физика (ауыспалы)") 
                else: todays_subjects.insert(1, "Ағылшын тілі (ауыспалы)")
            elif day_of_week == 4:
                if is_even_week: todays_subjects.append("География (ауыспалы)")
                else: todays_subjects.append("Дүниежүзі тарихы (ауыспалы)")
            
            if not todays_subjects: 
                subject_options = ["Бүгін сабақ жоқ", "Басқа пән (төменге жазыңыз)"]
            else:
                subject_options = ["Пәнді таңдаңыз..."] + todays_subjects + ["Басқа пән (төменге жазыңыз)"]
            
            selected_subject = st.selectbox(
                "📓 Пәнді таңдаңыз", 
                options=subject_options,
                index=0
            )

        other_subject = ""
        if selected_subject == "Басқа пән (төменге жазыңыз)":
            other_subject = st.text_input("Пәннің атын жазыңыз:", placeholder="Мыс: Электив")

    st.divider()

    # 2. КАРТОЧКА: Бағалау (Форманың ішінде)
    with sac.card(title="2. Бағалау мәліметтері", icon="pencil-fill", color='red'):
        with st.form("grade_form"):
            selected_student = st.selectbox(
                "🧑‍🎓 Студенттің аты-жөні", 
                options=STUDENT_LIST,
                index=0
            )
            grade = st.number_input(
                "💯 Баға (0-100)", 
                min_value=0.0, 
                max_value=100.0, 
                value=75.0,
                step=1.0
            )
            comment = st.text_area(
                "✍️ Түсініктеме (міндетті емес)", 
                placeholder="Мысалы: Үй жұмысы №3, CӨЖ-1, Сабақтағы белсенділік..."
            )
            st.divider()
            submitted = st.form_submit_button("💾 Бағаны сақтау", type="primary", use_container_width=True)

    # --- Сақтау логикасы (Карточкадан тыс) ---
    if submitted:
        final_subject = other_subject if selected_subject == "Басқа пән (төменге жазыңыз)" else selected_subject
        
        if final_subject == "Пәнді таңдаңыз..." or final_subject == "Бүгін сабақ жоқ" or not final_subject:
            sac.alert(label='Пәнді таңдаңыз немесе жазыңыз.', icon='warning', color='orange')
        elif selected_student == "Студентті таңдаңыз...": 
            sac.alert(label='Студентті таңдаңыз.', icon='warning', color='orange')
        else:
            with st.spinner(f"'{selected_student}' үшін баға сақталуда..."):
                client = connect_to_gsheet()
                if client:
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    data_to_save = [
                        selected_day.strftime("%Y-%m-%d"),
                        final_subject,
                        selected_student,
                        grade,
                        comment,
                        current_time
                    ]
                    if save_to_gsheet(client, GOOGLE_SHEET_NAME, data_to_save):
                        sac.alert(
                            label=f"{selected_day.strftime('%d.%m.%Y')} күнгі '{final_subject}' пәнінен '{selected_student}' үшін баға ({grade}) сәтті сақталды!", 
                            icon='check-circle-fill', 
                            color='green'
                        )
                        st.balloons()
                    else:
                        sac.alert(label='Деректерді Google Sheet-ке сақтау кезінде қате орын алды.', icon='x-circle-fill', color='red')

# --- БӨЛІМ 3: САБАҚ КЕСТЕСІ ---
if selected_tab == "🗓️ Сабақ кестесі":
    st.subheader("БҚ2503 тобының сабақ кестесі")
    try:
        st.image(
            "2025-11-24 23.56.03.jpg", 
            caption="Ресми сабақ кестесі (Суретті үлкейту үшін басыңыз)"
        )
    except Exception as e:
        st.error(f"⚠️ Cабақ кестесінің суретін жүктеу кезінде қате кетті.")
        st.warning("Суретті ('2025-11-24 23.56.03.jpg') GitHub репозиторийіңізге жүктегеніңізді тексеріп, 'Reboot' жасаңыз.")

# --- БӨЛІМ 4: ХАБАРЛАНДЫРУЛАР (ДИЗАЙН ЖАҢАРТЫЛДЫ) ---
if selected_tab == "🔔 Хабарландырулар":
    st.subheader("📢 Соңғы жаңалықтар мен хабарландырулар")
    st.write("Мұнда топқа қатысты маңызды ақпарат жарияланып тұрады.")
    
    st.divider()

    # sac.alert() әлдеқайда әдемі көрінеді
    sac.alert(
        label='Маңызды (Дедлайн)',
        description=" 'Физика' пәнінен СӨЖ-1 жұмысын осы жұмаға (28.11.2025) дейін тапсыру керек!",
        icon='fire',
        color='red',
        closable=True
    )
    
    sac.alert(
        label='Жалпы хабарлама',
        description="Ертең, 26.11.2025 (сәрсенбі), сабақтар 1 сағатқа қысқартылады. Себебі - оқытушылар жиналысы.",
        icon='info-circle-fill',
        color='blue',
        closable=True
    )
    
    sac.alert(
        label='Құттықтаймыз!',
        description="'Информатика' пәнінен өткен олимпиадада біздің топтан Қабиден Йусуф 1-орын алды.",
        icon='trophy-fill',
        color='green',
        closable=True
    )

    sac.alert(
        label='Сабақ болмайды',
        description="'Дене тәрбиесі' пәнінің оқытушысы ауырып қалуына байланысты бүгін (25.11.2025) соңғы сабақ болмайды.",
        icon='exclamation-triangle-fill',
        color='orange',
        closable=True
    )
    
    st.markdown("""
    ---
    #### Мұрағат (Ескі жаңалықтар)
    * *15.11.2025: Ағылшын тілінен эссе тапсырылды.*
    * *10.11.2025: Колледж ауласын тазалауға арналған сенбілік.*
    """)
