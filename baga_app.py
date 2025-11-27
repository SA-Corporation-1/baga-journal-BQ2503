import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
# Бұл кітапхана gspread пен pandas-ты біріктіруге өте ыңғайлы
from gspread_dataframe import get_as_dataframe, set_with_dataframe

# --- 0. Парақ баптаулары ---
st.set_page_config(
    page_title="BQ 2503",
    page_icon="📋",
    layout="wide"
)

# --- 1. Google Sheets Баптаулары ---
GOOGLE_SHEET_NAME = "Студенттердің бағалары" # Сіздің Google Sheet файлыңыздың аты
WORKSHEET_NAME = "Лист1" # Сіздің CSV файлыңыздың аты осылай екенін көрсетті

# --- 2. Google Sheets Функциялары ---

@st.cache_resource(ttl=3600)
def connect_to_gsheet():
    """Google Sheets-ке бір рет қосылу."""
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
        st.warning("`secrets.toml` файлыңыздың дұрыстығын тексеріңіз.")
        return None

@st.cache_data(ttl=60) # Деректерді 60 секунд сайын жаңарту
def load_data_from_sheet(_client, sheet_name, worksheet_name):
    """Ведомостьты DataFrame ретінде оқу."""
    try:
        # 'client' орнына '_client' қолданамыз
        sheet = _client.open(sheet_name).worksheet(worksheet_name) 
        
        # 1-қатарды баған (header) ретінде оқу
        df = get_as_dataframe(sheet, header=0) 
        
        # 'Unnamed: 0' деген артық баған пайда болса, оны алып тастау
        if 'Unnamed: 0' in df.columns:
            df = df.drop(columns=['Unnamed: 0'])
        
        # 'Студент Аты' бағанын өңдеу
        if 'Студент Аты' in df.columns:
             df = df.set_index('Студент Аты')
        
        return df
    
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"'{worksheet_name}' атты парақ (worksheet) табылмады.")
        st.info(f"Google Sheet файлыңызда '{worksheet_name}' атты парақ барына көз жеткізіңіз.")
        return None
    except Exception as e:
        st.error(f"Ведомостьты оқу кезінде қате: {e}")
        return None

def save_data_to_sheet(client, sheet_name, worksheet_name, df_to_save):
    """Өңделген DataFrame-ді Google Sheet-ке толығымен сақтау."""
    try:
        sheet = client.open(sheet_name).worksheet(worksheet_name)
        
        # Индексті қайтадан бағанға айналдыру (мысалы, 'Студент Аты')
        df_to_save = df_to_save.reset_index()
        
        # Google Sheet-ті толығымен тазалап, жаңа деректерді жазу
        set_with_dataframe(sheet, df_to_save, resize=True)
        return True
    except Exception as e:
        st.error(f"Ведомостьты сақтау кезінде қате: {e}")
        return False

# --- 3. Streamlit Интерфейсі ---

st.title("📋 BQ 2503")
st.markdown(f"**Google Sheet:** `{GOOGLE_SHEET_NAME}` / **Парақ:** `{WORKSHEET_NAME}`")

client = connect_to_gsheet()

if client:
    # 1. Деректерді жүктеу
    df = load_data_from_sheet(client, GOOGLE_SHEET_NAME, WORKSHEET_NAME)
    
    if df is not None:
        if df.empty:
            st.warning(f"'{WORKSHEET_NAME}' парағы бос. Google Sheet-ке барып, кем дегенде баған аттарын (пәндер) және бір студентті енгізіңіз.")
        else:
            st.success("Деректер сәтті оқылды. Төмендегі кестені өңдей аласыз.")
            
            # --- 2. НЕГІЗГІ РЕДАКТОР ---
            # 'df_editor' сессия күйінде сақталады, 
            # бұл батырманы басқанда өзгерістердің жоғалып кетпеуіне кепілдік береді
            if 'df_editor' not in st.session_state:
                st.session_state.df_editor = df.copy()

            # st.data_editor өзгерістерді автоматты түрде 'st.session_state.df_editor' ішінде сақтайды
            edited_df = st.data_editor(
                st.session_state.df_editor,
                num_rows="dynamic", # Жаңа студент қосу/өшіруге рұқсат
                use_container_width=True,
                height=600 # Кестенің биіктігі
            )
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            # --- 3. Сақтау батырмасы ---
            if col1.button("💾 Өзгерістерді Google Sheet-ке сақтау", type="primary", use_container_width=True):
                with st.spinner("Сақталуда..."):
                    # Өңделген деректерді (edited_df) сақтау
                    if save_data_to_sheet(client, GOOGLE_SHEET_NAME, WORKSHEET_NAME, edited_df):
                        st.success("✅ Ведомость сәтті жаңартылды!")
                        st.balloons()
                        # Кэшті тазалап, деректерді қайта жүктеу
                        st.cache_data.clear()
                        st.session_state.df_editor = edited_df.copy() # Жаңартылған күйді сақтау
                    else:
                        st.error("❌ Сақтау кезінде қате орын алды.")

            # --- 4. Қайта жүктеу батырмасы ---
            if col2.button("🔄 Google Sheet-тен қайта жүктеу", use_container_width=True):
                st.cache_data.clear()
                st.session_state.df_editor = load_data_from_sheet(client, GOOGLE_SHEET_NAME, WORKSHEET_NAME)
                st.info("Деректер Google Sheet-тен қайта жүктелді.")
                st.rerun() # Бетті жаңарту

else:
    st.error("Google Sheets-ке қосылу мүмкін болмады. `secrets.toml` файлын тексеріңіз.")
