import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="ACTIVITY LOG", page_icon="📊", initial_sidebar_state="expanded")

# Apply dark mode
st.markdown(
    """
    <style>
    .reportview-container {
        background: #2E2E2E;
        color: white;
    }
    .sidebar .sidebar-content {
        background: #2E2E2E;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title('ACTIVITY LOG')

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file)

    # Convert 'Date' to datetime if it isn't already
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Exclude rows where the date is a Sunday (weekday() == 6)
    df = df[df['Date'].dt.weekday != 6]  # 6 corresponds to Sunday

    return df

def process_data(df):
    # Extract date only from 'First Login Time' (assuming it is in datetime format)
    df['Login Date'] = pd.to_datetime(df['First Login Time'], errors='coerce').dt.date

    # Extract first name from 'Collector' (assuming the format is "First Last")
    df['Collector'] = df['Collector'].apply(lambda x: x.split()[0] if isinstance(x, str) else '')

    # Extract access type (assuming values are like 'Collector', 'Collector (All Accounts)', etc.)
    df['Access'] = df['Access'].apply(lambda x: x.split()[0] if isinstance(x, str) else '')

    # Extract time from 'First Login Time' (assuming it is in datetime format)
    df['First Login Time'] = pd.to_datetime(df['First Login Time'], errors='coerce').dt.strftime('%H:%M:%S')

    # Determine if "On Time" or "Late" based on login time
    def check_on_time(row):
        login_time = pd.to_datetime(row['First Login Time'], format='%H:%M:%S').time()
        
        # Define the two schedules
        schedule_1 = pd.to_datetime('08:00:00', format='%H:%M:%S').time()
        schedule_2 = pd.to_datetime('10:00:00', format='%H:%M:%S').time()

        if login_time <= schedule_1:
            return 'ON TIME'
        elif schedule_1 < login_time <= pd.to_datetime('08:30:00', format='%H:%M:%S').time():
            return 'LATE'
        elif schedule_2 <= login_time <= pd.to_datetime('10:30:00', format='%H:%M:%S').time():
            return 'ON TIME'
        elif login_time > pd.to_datetime('10:30:00', format='%H:%M:%S').time():
            return 'LATE'
        return 'UNKNOWN'

    df['On Time or Late'] = df.apply(check_on_time, axis=1)

    # Select only relevant columns for the summary
    summary_df = df[['Login Date', 'Collector', 'Access', 'First Login Time', 'On Time or Late']]

    return summary_df

uploaded_file = st.sidebar.file_uploader("Upload Daily Remark File", type="xlsx")

if uploaded_file:
    df = load_data(uploaded_file)
    summary_df = process_data(df)
    
    # Display the summary table
    st.write(summary_df)
