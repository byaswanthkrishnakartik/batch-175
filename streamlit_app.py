import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import time
from datetime import datetime, timedelta

# Styling
sns.set(style="whitegrid")

# Database setup
DB_FILE = "hospital_maintenance.db"

# Connect to DB and create table if it doesn't exist
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS equipment (
            id TEXT PRIMARY KEY,
            type TEXT,
            last_maintenance TEXT,
            next_maintenance TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    return conn

# Populate with dummy data if empty
def seed_data(conn):
    df = pd.read_sql_query("SELECT * FROM equipment", conn)
    if df.empty:
        data = []
        for i in range(30):
            eid = f"EQUIP{str(i+1).zfill(4)}"
            etype = np.random.choice(['X-ray', 'MRI', 'CT Scan', 'Ultrasound', 'Ventilator'])
            last = datetime.now() - timedelta(days=np.random.randint(30, 180))
            next_ = last + timedelta(days=np.random.randint(30, 90))
            status = np.random.choice(['Operational', 'Under Maintenance', 'Faulty'])
            data.append((eid, etype, last.isoformat(), next_.isoformat(), status))
        conn.executemany("INSERT INTO equipment VALUES (?, ?, ?, ?, ?)", data)
        conn.commit()

# Fetch data from DB
def load_data(conn):
    df = pd.read_sql_query("SELECT * FROM equipment", conn)
    df['Last Maintenance Date'] = pd.to_datetime(df['last_maintenance'])
    df['Next Maintenance Date'] = pd.to_datetime(df['next_maintenance'])
    df['Days Since Last Maintenance'] = (datetime.now() - df['Last Maintenance Date']).dt.days
    df['Maintenance Urgency'] = df['Days Since Last Maintenance'].apply(
        lambda x: 'High' if x > 180 else ('Medium' if x > 90 else 'Low')
    )
    return df

# Request maintenance
def request_maintenance(conn, eid):
    new_date = datetime.now() + timedelta(days=np.random.randint(30, 60))
    conn.execute("""
        UPDATE equipment
        SET status='Under Maintenance', next_maintenance=?
        WHERE id=?
    """, (new_date.isoformat(), eid))
    conn.commit()

# Delete equipment
def delete_equipment(conn, eid):
    conn.execute("DELETE FROM equipment WHERE id=?", (eid,))
    conn.commit()

# Add equipment
def add_equipment(conn, eid, etype, status):
    last = datetime.now() - timedelta(days=np.random.randint(30, 180))
    next_ = last + timedelta(days=np.random.randint(30, 90))
    conn.execute("""
        INSERT INTO equipment (id, type, last_maintenance, next_maintenance, status)
        VALUES (?, ?, ?, ?, ?)
    """, (eid, etype, last.isoformat(), next_.isoformat(), status))
    conn.commit()

# App Title
st.markdown("""
    <h1 style='text-align: center;'>🏥 Hospital Facility Management</h1>
    <h2 style='text-align: center;'>🎓 Batch 175</h2>
""", unsafe_allow_html=True)

# Database Connection
conn = init_db()
seed_data(conn)

# Load and display data
data = load_data(conn)
st.subheader("🔍 Equipment Inventory")
st.dataframe(data[['id', 'type', 'Last Maintenance Date', 'Next Maintenance Date', 'status']])

# Visualizations
st.subheader("📊 Equipment Status Distribution")
fig1, ax1 = plt.subplots()
sns.countplot(data=data, x='status', palette='viridis', ax=ax1)
st.pyplot(fig1)

st.subheader("⚠️ Maintenance Urgency Levels")
fig2, ax2 = plt.subplots()
sns.countplot(data=data, x='Maintenance Urgency', palette='Blues_d', ax=ax2)
st.pyplot(fig2)

# Maintenance due soon
st.subheader("🛠️ Maintenance Due in Next 60 Days")
upcoming = data[data['Next Maintenance Date'] < datetime.now() + timedelta(days=60)]
st.dataframe(upcoming[['id', 'Next Maintenance Date']])

# Request maintenance
st.subheader("🔧 Request Maintenance")
eid_input = st.text_input("Enter Equipment ID to request maintenance:")
if st.button("Request Maintenance"):
    if eid_input in data['id'].values:
        request_maintenance(conn, eid_input)
        st.success(f"✅ Maintenance requested for {eid_input}")
        time.sleep(5)
        st.rerun()
    else:
        st.error("❌ Equipment ID not found!")

# Delete equipment
st.subheader("🗑️ Delete Equipment Record")
eid_delete = st.text_input("Enter Equipment ID to delete:", key="delete")
if st.button("Delete Equipment"):
    if eid_delete in data['id'].values:
        delete_equipment(conn, eid_delete)
        st.success(f"🗑️ Equipment {eid_delete} deleted.")
        time.sleep(5)
        st.rerun()
    else:
        st.error("❌ Equipment ID not found!")

# Add equipment
st.subheader("➕ Add New Equipment")
eid_add = st.text_input("Enter new Equipment ID:", key="add")
etype_add = st.selectbox("Select Equipment Type:", ['X-ray', 'MRI', 'CT Scan', 'Ultrasound', 'Ventilator', 'ECG machine', 'EEG machine', 'EMG machine', 'Blood Gas Analyzers', 'Defibrillators', 'Hospital Beds'])
status_add = st.selectbox("Select Status:", ['Operational', 'Under Maintenance', 'Faulty'])
if st.button("Add Equipment"):
    if eid_add in data['id'].values:
        st.error("❌ Equipment ID already exists!")
    else:
        add_equipment(conn, eid_add, etype_add, status_add)
        st.success(f"✅ Equipment {eid_add} added.")
        time.sleep(5)
        st.rerun()

# Mark equipment as operational
st.subheader("✅ Mark Equipment as Operational")
# Only show IDs with 'Under Maintenance' status
maintenance_items = data[data['status'] == 'Under Maintenance']
eid_operational = st.selectbox("Select Equipment ID to mark as operational:", maintenance_items['id'].values)
if st.button("Mark as Operational"):
    if eid_operational:
        conn.execute("""
            UPDATE equipment
            SET status='Operational'
            WHERE id=?
        """, (eid_operational,))
        conn.commit()
        st.success(f"✅ Equipment {eid_operational} marked as Operational.")
        time.sleep(5)
        st.rerun()
    else:
        st.error("❌ No equipment selected!")
