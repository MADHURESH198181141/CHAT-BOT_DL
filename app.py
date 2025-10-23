# app.py

import streamlit as st
import pandas as pd
import numpy as np
import time
import sqlite3

# --- Page Configuration ---
st.set_page_config(
    page_title="Real-Time Patient Health Monitor",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Database Setup ---
DB_FILE = "/app/data/patient_data.db"

def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Create patients table
    c.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            age INTEGER,
            gender TEXT,
            room_number TEXT
        )
    ''')
    # Create vitals table with a foreign key to the patients table
    c.execute('''
        CREATE TABLE IF NOT EXISTS vitals (
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            patient_id INTEGER,
            heart_rate REAL,
            temperature REAL,
            spo2 REAL,
            systolic_bp REAL,
            diastolic_bp REAL,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    # Add sample data if the patients table is empty
    c.execute("SELECT COUNT(*) FROM patients")
    if c.fetchone()[0] == 0:
        sample_patients = [
            ('John Smith', 45, 'Male', '101A'),
            ('Jane Doe', 62, 'Female', '102B'),
            ('Peter Jones', 78, 'Male', '103A'),
            ('Mary Johnson', 55, 'Female', '104C')
        ]
        c.executemany('INSERT INTO patients (name, age, gender, room_number) VALUES (?, ?, ?, ?)', sample_patients)
    conn.commit()
    conn.close()

def add_patient(name, age, gender, room_number):
    """Adds a new patient to the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('INSERT INTO patients (name, age, gender, room_number) VALUES (?, ?, ?, ?)',
                  (name, age, gender, room_number))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # This error occurs if the patient name is not unique
        return False

def get_patients():
    """Fetches all patients from the database."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM patients", conn)
    conn.close()
    return df

def get_patient_details(patient_id):
    """Fetches details for a specific patient."""
    conn = sqlite3.connect(DB_FILE)
    patient_details = pd.read_sql_query(f"SELECT * FROM patients WHERE id = {patient_id}", conn)
    conn.close()
    return patient_details.iloc[0] if not patient_details.empty else None

def add_vitals(patient_id, heart_rate, temperature, spo2, systolic, diastolic):
    """Adds a new set of vital signs for a specific patient."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO vitals (patient_id, heart_rate, temperature, spo2, systolic_bp, diastolic_bp) VALUES (?, ?, ?, ?, ?, ?)',
              (patient_id, heart_rate, temperature, spo2, systolic, diastolic))
    conn.commit()
    conn.close()

def get_vitals_for_patient(patient_id):
    """Fetches all vitals data for a specific patient."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM vitals WHERE patient_id = {patient_id} ORDER BY timestamp DESC", conn)
    conn.close()
    return df

# --- Vital Signs Safe Ranges and Alert Logic (Unchanged) ---
HEART_RATE_RANGE = {'normal': (60, 100), 'moderate': (50, 110)}
TEMPERATURE_RANGE = {'normal': (36.5, 37.5), 'moderate': (36.0, 38.0)}
SPO2_RANGE = {'normal': (95, 100), 'moderate': (90, 100)}
BP_RANGE = {'normal': (90, 120, 60, 80), 'moderate': (85, 130, 55, 85)}

def get_alert_status(metric, value):
    if metric == 'Heart Rate':
        ranges = HEART_RATE_RANGE
        if ranges['normal'][0] <= value <= ranges['normal'][1]: return "🟢 Normal"
        elif ranges['moderate'][0] <= value <= ranges['moderate'][1]: return "🟡 Moderate"
        else: return "🔴 High-Risk"
    elif metric == 'Temperature':
        ranges = TEMPERATURE_RANGE
        if ranges['normal'][0] <= value <= ranges['normal'][1]: return "🟢 Normal"
        elif ranges['moderate'][0] <= value <= ranges['moderate'][1]: return "🟡 Moderate"
        else: return "🔴 High-Risk"
    elif metric == 'SpO2':
        ranges = SPO2_RANGE
        if value >= ranges['normal'][0]: return "🟢 Normal"
        elif value >= ranges['moderate'][0]: return "🟡 Moderate"
        else: return "🔴 High-Risk"
    elif metric == 'Blood Pressure':
        sys, dia = value
        norm, mod = BP_RANGE['normal'], BP_RANGE['moderate']
        if (norm[0] <= sys <= norm[1]) and (norm[2] <= dia <= norm[3]): return "🟢 Normal"
        elif (mod[0] <= sys <= mod[1]) and (mod[2] <= dia <= mod[3]): return "🟡 Moderate"
        else: return "🔴 High-Risk"
    return ""

# --- Main Application ---
# Initialize DB
init_db()

st.title("🏥 Real-Time Patient Health Monitoring System")

# --- Sidebar ---
st.sidebar.title("Controls")

# --- NEW: Add Patient Form ---
with st.sidebar.expander("➕ Add a New Patient", expanded=False):
    with st.form("new_patient_form", clear_on_submit=True):
        new_name = st.text_input("Name")
        new_age = st.number_input("Age", min_value=0, max_value=120, step=1)
        new_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        new_room = st.text_input("Room Number")
        submitted = st.form_submit_button("Add Patient")

        if submitted:
            if new_name and new_room:
                if add_patient(new_name, new_age, new_gender, new_room):
                    st.success(f"Patient '{new_name}' added successfully!")
                else:
                    st.error(f"Patient with name '{new_name}' already exists.")
            else:
                st.error("Name and Room Number are required fields.")

# --- Patient Selection ---
st.sidebar.title("Patient List")
patients_df = get_patients()
if not patients_df.empty:
    patient_id_map = {name: id for id, name in zip(patients_df['id'], patients_df['name'])}
    selected_patient_name = st.sidebar.selectbox("Select a Patient to Monitor", patient_id_map.keys())
    selected_patient_id = patient_id_map[selected_patient_name]

    # --- Display Selected Patient Details ---
    st.header(f"Monitoring Dashboard for: {selected_patient_name}")
    patient_details = get_patient_details(selected_patient_id)
    col1, col2, col3 = st.columns(3)
    col1.metric("Age", patient_details['age'])
    col2.metric("Gender", patient_details['gender'])
    col3.metric("Room No.", patient_details['room_number'])
    st.markdown("<hr/>", unsafe_allow_html=True)

    # Placeholder for real-time components
    placeholder = st.empty()

    # --- Background Data Simulation ---
    def simulate_all_patients_data(all_patient_ids):
        for patient_id in all_patient_ids:
            heart_rate = np.random.randint(55, 115)
            temperature = round(np.random.uniform(35.8, 38.5), 1)
            spo2 = np.random.randint(88, 101)
            systolic_bp = np.random.randint(80, 140)
            diastolic_bp = np.random.randint(50, 90)
            add_vitals(patient_id, heart_rate, temperature, spo2, systolic_bp, diastolic_bp)

    # --- Real-time Update Loop ---
    while True:
        simulate_all_patients_data(patients_df['id'].tolist())
        vitals_df = get_vitals_for_patient(selected_patient_id)

        if not vitals_df.empty:
            latest_data = vitals_df.iloc[0]
            with placeholder.container():
                # Display metrics, charts, and table as before
                st.subheader("Current Vital Signs")
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                with m_col1:
                    st.metric("❤️ Heart Rate (bpm)", f"{latest_data['heart_rate']:.0f}")
                    st.write(get_alert_status('Heart Rate', latest_data['heart_rate']))
                with m_col2:
                    st.metric("🌡️ Body Temperature (°C)", f"{latest_data['temperature']:.1f}")
                    st.write(get_alert_status('Temperature', latest_data['temperature']))
                with m_col3:
                    st.metric("💨 SpO₂ (%)", f"{latest_data['spo2']:.0f}")
                    st.write(get_alert_status('SpO2', latest_data['spo2']))
                with m_col4:
                    bp_val = f"{latest_data['systolic_bp']:.0f}/{latest_data['diastolic_bp']:.0f}"
                    st.metric("🩸 Blood Pressure (mmHg)", bp_val)
                    st.write(get_alert_status('Blood Pressure', (latest_data['systolic_bp'], latest_data['diastolic_bp'])))

                st.markdown("<hr/>", unsafe_allow_html=True)
                st.subheader("Vital Signs History")
                history_df = vitals_df.head(50).iloc[::-1]
                st.line_chart(history_df.rename(columns={'timestamp':'index'}).set_index('index')[['heart_rate', 'temperature', 'spo2']])

                st.subheader("Patient Data Log")
                st.dataframe(vitals_df)
        else:
            with placeholder.container():
                st.warning("No data available for this patient yet. Waiting for new readings...")

        time.sleep(5)
else:
    st.warning("No patients in the database. Please add a patient using the sidebar.")