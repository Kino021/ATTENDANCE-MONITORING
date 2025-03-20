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

    # Print the column names to debug
    st.write("Column names in the uploaded file:")
    st.write(df.columns)

    # Check if 'Date' column exists, and if not, print all columns
    if 'Date' not in df.columns:
        st.error("The 'Date' column was not found in the file. Please check the column names.")
        return None

    # Convert 'Date' to datetime if it isn't already
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    # Exclude rows where the date is a Sunday (weekday() == 6)
    df = df[df['Date'].dt.weekday != 6]  # 6 corresponds to Sunday

    return df

uploaded_file = st.sidebar.file_uploader("Upload Daily Remark File", type="xlsx")

if uploaded_file:
    df = load_data(uploaded_file)
    if df is not None:
         # Initialize an empty DataFrame for the summary table by collector
        collector_summary = pd.DataFrame(columns=[ 
            'Day', 'Collector', 'Client', 'Manual Accounts', 'Total Manual Calls', 'Predictive Accounts', 'Predictive Dial', 'Total Connected', 'Total PTP', 'Total RPC', 'PTP Amount', 'Balance Amount', 'Total Talk Time'
        ])

        # Define exclude_users if necessary (or remove if not applicable)
        exclude_users = []  # Add users to exclude if needed (e.g., system users)

        # Function to convert seconds to HH:MM:SS format
        def seconds_to_hms(seconds):
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        # Group by 'Date', 'Remark By' (Collector), and 'Client' (Campaign)
        for (date, collector, client), collector_group in filtered_df[~filtered_df['Remark By'].str.upper().isin(['SYSTEM'])].groupby([filtered_df['Date'].dt.date, 'Remark By', 'Client']):

            # Calculate the metrics
            total_connected = collector_group[collector_group['Call Status'] == 'CONNECTED']['Account No.'].count()
            total_ptp = collector_group[collector_group['Status'].str.contains('PTP', na=False) & (collector_group['PTP Amount'] != 0)]['Account No.'].nunique()
            total_rpc = collector_group[collector_group['Status'].str.contains('RPC', na=False)]['Account No.'].nunique()
            ptp_amount = collector_group[collector_group['Status'].str.contains('PTP', na=False) & (collector_group['PTP Amount'] != 0)]['PTP Amount'].sum()

            # Filter rows where PTP Amount is not zero for balance calculation
            balance_amount = collector_group[(collector_group['Status'].str.contains('PTP', na=False)) & (collector_group['PTP Amount'] != 0)]['Balance'].sum()

            # Add the total manual calls (filter rows based on Remark Type as "OUTGOING")
            total_manual_calls = collector_group[collector_group['Remark Type'].str.contains('OUTGOING', case=False, na=False) & 
                                                ~collector_group['Remark By'].isin(exclude_users)].shape[0]

            # Calculate the unique manual accounts (distinct Account No.)
            manual_accounts = collector_group[collector_group['Remark Type'].str.contains('OUTGOING', case=False, na=False)]['Account No.'].nunique()

            # Calculate Predictive Dial count for "FOLLOW UP" or "PREDICTIVE" remarks
            predictive_dial = collector_group[collector_group['Remark Type'].str.contains('FOLLOW UP|PREDICTIVE', case=False, na=False)]['Account No.'].count()

            # Calculate Predictive Accounts (unique Account No. for "FOLLOW UP" or "PREDICTIVE" remarks)
            predictive_accounts = collector_group[collector_group['Remark Type'].str.contains('FOLLOW UP|PREDICTIVE', case=False, na=False)]['Account No.'].nunique()

            # Calculate the total talk time (in seconds), ensure it's numeric
            total_talk_time = pd.to_numeric(collector_group['Talk Time Duration'], errors='coerce').sum()  # Sum of talk time in seconds
            total_talk_time_hms = seconds_to_hms(total_talk_time)  # Convert to HH:MM:SS format

            # Add the row to the summary with Total Manual Calls after Collector
            collector_summary = pd.concat([collector_summary, pd.DataFrame([{
                'Day': date,
                'Collector': collector,
                'Client': client,  # Add the Client (Campaign)
                'Manual Accounts': manual_accounts,  # Add the Manual Accounts count here
                'Total Manual Calls': total_manual_calls,  # Add Total Manual Calls here
                'Predictive Accounts': predictive_accounts,  # Add Predictive Accounts count first
                'Predictive Dial': predictive_dial,  # Add Predictive Dial count second
                'Total Connected': total_connected,
                'Total PTP': total_ptp,
                'Total RPC': total_rpc,
                'PTP Amount': ptp_amount,
                'Balance Amount': balance_amount,
                'Total Talk Time': total_talk_time_hms  # Use the HH:MM:SS format here
            }])], ignore_index=True)

        # Calculate and append totals for the collector summary
        total_manual_calls = collector_summary['Total Manual Calls'].sum()  # Total Manual Calls count across all collectors
        total_predictive_dial = collector_summary['Predictive Dial'].sum()  # Total Predictive Dial count across all collectors
        total_predictive_accounts = collector_summary['Predictive Accounts'].sum()  # Total Predictive Accounts count across all collectors
        total_talk_time_seconds = collector_summary['Total Talk Time'].apply(lambda x: sum([int(i) * factor for i, factor in zip(x.split(":"), [3600, 60, 1])])).sum()  # Convert HH:MM:SS to seconds

        # Convert total talk time to HH:MM:SS format for total row
        total_talk_time_hms = seconds_to_hms(total_talk_time_seconds)

        # Count the number of unique collectors
        total_collectors = collector_summary['Collector'].nunique()

        total_row = pd.DataFrame([{
            'Day': 'Total',
            'Collector': total_collectors,  # Just the count of collectors
            'Client': '',  # No campaign for the total row
            'Manual Accounts': collector_summary['Manual Accounts'].sum(),  # Sum of Manual Accounts across all rows
            'Total Manual Calls': total_manual_calls,
            'Predictive Accounts': total_predictive_accounts,  # Add the total Predictive Accounts count first
            'Predictive Dial': total_predictive_dial,  # Add the total Predictive Dial count second
            'Total Connected': collector_summary['Total Connected'].sum(),
            'Total PTP': collector_summary['Total PTP'].sum(),
            'Total RPC': collector_summary['Total RPC'].sum(),
            'PTP Amount': collector_summary['PTP Amount'].sum(),
            'Balance Amount': collector_summary['Balance Amount'].sum(),
            'Total Talk Time': total_talk_time_hms  # Show total talk time in HH:MM:SS format
        }])

        # Remove the total row before sorting
        collector_summary_without_total = collector_summary[collector_summary['Day'] != 'Total']

        # Sort by 'Total PTP' in descending order for per-collector rows
        collector_summary_without_total = collector_summary_without_total.sort_values(by='Total PTP', ascending=False)

        # Add the total row back at the end
        collector_summary = pd.concat([collector_summary_without_total, total_row], ignore_index=True)

        # Round off numeric columns to 2 decimal places
        collector_summary[['PTP Amount', 'Balance Amount']] = collector_summary[['PTP Amount', 'Balance Amount']].round(2)

        # Reorder columns to ensure Predictive Accounts comes before Predictive Dial
        column_order = ['Day', 'Collector', 'Client', 'Manual Accounts', 'Total Manual Calls', 'Predictive Accounts', 'Predictive Dial', 'Total Connected', 'Total PTP', 'Total RPC', 'PTP Amount', 'Balance Amount', 'Total Talk Time']
        collector_summary = collector_summary[column_order]

        st.write(collector_summary)
