import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide", page_title="Daily Remark Summary", page_icon="📊", initial_sidebar_state="expanded")

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

st.title('Daily Remark Summary')

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file)

    # Convert 'Date' to datetime if it isn't already
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Exclude rows where the date is a Sunday (weekday() == 6)
    df = df[df['Date'].dt.weekday != 6]  # 6 corresponds to Sunday

    return df

uploaded_file = st.sidebar.file_uploader("Upload Daily Remark File", type="xlsx")

if uploaded_file:
    df = load_data(uploaded_file)

    # Extract "Date"
    df['Date'] = df['Date'].dt.date

    # Extract "Collector" (only first name part)
    df['Collector'] = df['Collector'].str.split().str[0]

    # Filter "Access" column to only include the required types
    valid_access = ["Collector (All Accounts)", "Collector", "Collector (All Accounts No SMS and Email)"]
    df = df[df['Access'].isin(valid_access)]

    # Extract "First Log In Time" and convert it to just the time (HH:MM:SS format)
    df['First Login Time'] = pd.to_datetime(df['First Login Time'], errors='coerce').dt.strftime('%H:%M:%S')

    # Define function to determine if "On Time" or "Late"
    def get_on_time_status(first_login_time):
        time_obj = datetime.strptime(first_login_time, '%H:%M:%S')
        if 0 <= time_obj.hour < 8 or (time_obj.hour == 8 and time_obj.minute == 0):
            return "ON TIME"
        elif (time_obj.hour == 8 and time_obj.minute > 0) or (time_obj.hour == 9 and time_obj.minute < 30):
            return "LATE"
        elif 9 < time_obj.hour < 10 or (time_obj.hour == 9 and time_obj.minute >= 30):
            return "ON TIME"
        else:
            return "LATE"

    # Apply the "On Time or Late" function
    df['On Time or Late'] = df['First Login Time'].apply(get_on_time_status)

    # Create the summary table with the selected columns
    summary_table = df[['Date', 'Collector', 'Access', 'First Login Time', 'On Time or Late']]

    # Display the summary table
    st.write("### Summary Table")
    st.dataframe(summary_table)
