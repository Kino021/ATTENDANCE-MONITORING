import streamlit as st
import pandas as pd

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

if uploaded_file is not None:
    df = load_data(uploaded_file)

    # Exclude rows where 'Debtor' contains 'DEFAULT_LEAD_'
    df = df[~df['Debtor'].str.contains("DEFAULT_LEAD_", case=False, na=False)]

    # Exclude rows where STATUS contains 'BP' (Broken Promise) or 'ABORT'
    df = df[~df['Status'].str.contains('ABORT', na=False)]

    # Exclude rows where REMARK contains certain keywords or phrases
    excluded_remarks = [
        "Broken Promise",
        "New files imported", 
        "Updates when case reassign to another collector", 
        "NDF IN ICS", 
        "FOR PULL OUT (END OF HANDLING PERIOD)", 
        "END OF HANDLING PERIOD"
    ]
    df = df[~df['Remark'].str.contains('|'.join(excluded_remarks), case=False, na=False)]

    # Exclude rows where "CALL STATUS" contains "OTHERS"
    df = df[~df['Call Status'].str.contains('OTHERS', case=False, na=False)]

    # Check if data is empty after filtering
    if df.empty:
        st.warning("No valid data available after filtering.")
    else:
        # Overall Combined Summary Table
        def calculate_combined_summary(df):
            summary_table = pd.DataFrame(columns=[ 
                'Day', 'TOTAL COLLECTORS', 'ACCOUNTS', 'TOTAL DIALED', 'PENETRATION RATE (%)', 'CONNECTED #', 
                'CONNECTED RATE (%)', 'CONNECTED ACC', 'PTP ACC', 'PTP RATE', 'TOTAL PTP AMOUNT', 
                'TOTAL BALANCE', 'CALL DROP #', 'SYSTEM DROP', 'CALL DROP RATIO #'
                 ]) 

            for date, group in df.groupby(df['Date'].dt.date):
                # Calculate total collectors by counting unique values in 'Remark By', excluding 'SYSTEM'
                total_collectors = group[~group['Remark By'].str.contains('SYSTEM', case=False, na=False)]['Remark By'].nunique()
                
                accounts = group[group['Remark Type'].isin(['Predictive', 'Follow Up', 'Outgoing'])]['Account No.'].nunique()
                total_dialed = group[group['Remark Type'].isin(['Predictive', 'Follow Up', 'Outgoing'])]['Account No.'].count()
                connected = group[group['Call Status'] == 'CONNECTED']['Account No.'].nunique()
                penetration_rate = (total_dialed / accounts * 100) if accounts != 0 else None
                connected_acc = group[group['Call Status'] == 'CONNECTED']['Account No.'].count()
                connected_rate = (connected_acc / total_dialed * 100) if total_dialed != 0 else None
                ptp_acc = group[(group['Status'].str.contains('PTP', na=False)) & (group['PTP Amount'] != 0)]['Account No.'].nunique()
                ptp_rate = (ptp_acc / connected * 100) if connected != 0 else None
                total_ptp_amount = group[(group['Status'].str.contains('PTP', na=False)) & (group['PTP Amount'] != 0)]['PTP Amount'].sum()
                total_balance = group[(group['PTP Amount'] != 0)]['Balance'].sum()  # Calculate total balance when PTP Amount exists
                system_drop = group[(group['Status'].str.contains('DROPPED', na=False)) & (group['Remark By'] == 'SYSTEM')]['Account No.'].count()
                call_drop_count = group[(group['Status'].str.contains('NEGATIVE CALLOUTS - DROP CALL', na=False)) & 
                                        (~group['Remark By'].str.upper().isin(['SYSTEM']))]['Account No.'].count()
                call_drop_ratio = (system_drop / connected_acc * 100) if connected_acc != 0 else None

                summary_table = pd.concat([summary_table, pd.DataFrame([{
                    'Day': date,
                    'ACCOUNTS': accounts,
                    'TOTAL COLLECTORS': total_collectors,
                    'TOTAL DIALED': total_dialed,
                    'PENETRATION RATE (%)': f"{round(penetration_rate)}%" if penetration_rate is not None else None,
                    'CONNECTED #': connected,
                    'CONNECTED RATE (%)': f"{round(connected_rate)}%" if connected_rate is not None else None,
                    'CONNECTED ACC': connected_acc,
                    'PTP ACC': ptp_acc,
                    'PTP RATE': f"{round(ptp_rate)}%" if ptp_rate is not None else None,
                    'TOTAL PTP AMOUNT': total_ptp_amount,
                    'TOTAL BALANCE': total_balance,
                    'CALL DROP #': call_drop_count,
                    'SYSTEM DROP': system_drop,
                    'CALL DROP RATIO #': f"{round(call_drop_ratio)}%" if call_drop_ratio is not None else None,
                }])], ignore_index=True)

            return summary_table

        # Display Combined Summary Table
        st.write("## Overall Combined Summary Table")
        combined_summary_table = calculate_combined_summary(df)
        st.write(combined_summary_table, container_width=True)

        # Overall Predictive Summary Table
        def calculate_predictive_summary(df):
            summary_table = pd.DataFrame(columns=[ 
                'Day', 'TOTAL COLLECTORS', 'ACCOUNTS', 'TOTAL DIALED', 'PENETRATION RATE (%)', 'CONNECTED #', 
                'CONNECTED RATE (%)', 'CONNECTED ACC', 'PTP ACC', 'PTP RATE', 'TOTAL PTP AMOUNT', 
                'TOTAL BALANCE', 'CALL DROP #', 'SYSTEM DROP', 'CALL DROP RATIO #'
            ]) 

            # Filter the dataframe to include only 'Follow Up' and 'Predictive' Remark Types
            df_filtered = df[df['Remark Type'].isin(['Predictive', 'Follow Up'])]

            for date, group in df_filtered.groupby(df_filtered['Date'].dt.date):
                # Calculate total collectors by counting unique values in 'Remark By', excluding 'SYSTEM'
                total_collectors = group[~group['Remark By'].str.contains('SYSTEM', case=False, na=False)]['Remark By'].nunique()
                
                accounts = group[group['Remark Type'].isin(['Predictive', 'Follow Up'])]['Account No.'].nunique()
                total_dialed = group[group['Remark Type'].isin(['Predictive', 'Follow Up'])]['Account No.'].count()
                connected = group[group['Call Status'] == 'CONNECTED']['Account No.'].nunique()
                penetration_rate = (total_dialed / accounts * 100) if accounts != 0 else None
                connected_acc = group[group['Call Status'] == 'CONNECTED']['Account No.'].count()
                connected_rate = (connected_acc / total_dialed * 100) if total_dialed != 0 else None
                ptp_acc = group[(group['Status'].str.contains('PTP', na=False)) & (group['PTP Amount'] != 0)]['Account No.'].nunique()
                ptp_rate = (ptp_acc / connected * 100) if connected != 0 else None
                total_ptp_amount = group[(group['Status'].str.contains('PTP', na=False)) & (group['PTP Amount'] != 0)]['PTP Amount'].sum()
                total_balance = group[(group['PTP Amount'] != 0)]['Balance'].sum()  # Calculate total balance when PTP Amount exists
                system_drop = group[(group['Status'].str.contains('DROPPED', na=False)) & (group['Remark By'] == 'SYSTEM')]['Account No.'].count()
                call_drop_count = group[(group['Status'].str.contains('NEGATIVE CALLOUTS - DROP CALL', na=False)) & 
                                        (~group['Remark By'].str.upper().isin(['SYSTEM']))]['Account No.'].count()
                call_drop_ratio = (system_drop / connected_acc * 100) if connected_acc != 0 else None

                summary_table = pd.concat([summary_table, pd.DataFrame([{
                    'Day': date,
                    'ACCOUNTS': accounts,
                    'TOTAL COLLECTORS': total_collectors,
                    'TOTAL DIALED': total_dialed,
                    'PENETRATION RATE (%)': f"{round(penetration_rate)}%" if penetration_rate is not None else None,
                    'CONNECTED #': connected,
                    'CONNECTED RATE (%)': f"{round(connected_rate)}%" if connected_rate is not None else None,
                    'CONNECTED ACC': connected_acc,
                    'PTP ACC': ptp_acc,
                    'PTP RATE': f"{round(ptp_rate)}%" if ptp_rate is not None else None,
                    'TOTAL PTP AMOUNT': total_ptp_amount,
                    'TOTAL BALANCE': total_balance,
                    'CALL DROP #': call_drop_count,
                    'SYSTEM DROP': system_drop,
                    'CALL DROP RATIO #': f"{round(call_drop_ratio)}%" if call_drop_ratio is not None else None,
                }])], ignore_index=True)

            return summary_table

        # Display Overall Predictive Summary Table
        st.write("## Overall Predictive Summary Table")
        overall_predictive_table = calculate_predictive_summary(df)
        st.write(overall_predictive_table)
        overall_manual_table = calculate_manual_summary(df)
        st.write(overall_manual_table)

        # Remaining summary functions can be handled in a similar manner as the predictive and manual summaries above.
        # Total Manual Summary Table
        def calculate_total_manual_summary(df):
    summary_table = pd.DataFrame(columns=[ 
        'TOTAL COLLECTORS', 'ACCOUNTS', 'TOTAL DIALED', 'PENETRATION RATE (%)', 'CONNECTED #', 
        'CONNECTED RATE (%)', 'CONNECTED ACC', 'PTP ACC', 'PTP RATE', 'TOTAL PTP AMOUNT', 
        'TOTAL BALANCE', 'CALL DROP #', 'SYSTEM DROP', 'CALL DROP RATIO #'
    ]) 

    # Filter the dataframe to include only 'Outgoing' Remark Type
    df_filtered = df[df['Remark Type'] == 'Outgoing']

    # Calculate total collectors by counting unique values in 'Remark By', excluding 'SYSTEM'
    total_collectors = df_filtered[~df_filtered['Remark By'].str.contains('SYSTEM', case=False, na=False)]['Remark By'].nunique()

    accounts = df_filtered['Account No.'].nunique()
    total_dialed = df_filtered['Account No.'].count()
    connected = df_filtered[df_filtered['Call Status'] == 'CONNECTED']['Account No.'].nunique()
    penetration_rate = (total_dialed / accounts * 100) if accounts != 0 else None
    connected_acc = df_filtered[df_filtered['Call Status'] == 'CONNECTED']['Account No.'].count()
    connected_rate = (connected_acc / total_dialed * 100) if total_dialed != 0 else None
    ptp_acc = df_filtered[(df_filtered['Status'].str.contains('PTP', na=False)) & (df_filtered['PTP Amount'] != 0)]['Account No.'].nunique()
    ptp_rate = (ptp_acc / connected * 100) if connected != 0 else None
    total_ptp_amount = df_filtered[(df_filtered['Status'].str.contains('PTP', na=False)) & (df_filtered['PTP Amount'] != 0)]['PTP Amount'].sum()
    total_balance = df_filtered[(df_filtered['PTP Amount'] != 0)]['Balance'].sum()
    system_drop = df_filtered[(df_filtered['Status'].str.contains('DROPPED', na=False)) & (df_filtered['Remark By'] == 'SYSTEM')]['Account No.'].count()
    call_drop_count = df_filtered[(df_filtered['Status'].str.contains('NEGATIVE CALLOUTS - DROP CALL', na=False)) & 
                                  (~df_filtered['Remark By'].str.upper().isin(['SYSTEM']))]['Account No.'].count()
    call_drop_ratio = (call_drop_count / connected_acc * 100) if connected_acc != 0 else None

    # Append the results to the summary table
    summary_table = pd.concat([summary_table, pd.DataFrame([{
        'TOTAL COLLECTORS': total_collectors,
        'ACCOUNTS': accounts,
        'TOTAL DIALED': total_dialed,
        'PENETRATION RATE (%)': f"{round(penetration_rate)}%" if penetration_rate is not None else None,
        'CONNECTED #': connected,
        'CONNECTED RATE (%)': f"{round(connected_rate)}%" if connected_rate is not None else None,
        'CONNECTED ACC': connected_acc,
        'PTP ACC': ptp_acc,
        'PTP RATE': f"{round(ptp_rate)}%" if ptp_rate is not None else None,
        'TOTAL PTP AMOUNT': total_ptp_amount,
        'TOTAL BALANCE': total_balance,
        'CALL DROP #': call_drop_count,
        'SYSTEM DROP': system_drop,
        'CALL DROP RATIO #': f"{round(call_drop_ratio)}%" if call_drop_ratio is not None else None,
    }])], ignore_index=True)

    return summary_table

        # Display Overall Predictive Summary Table
        st.write("## Overall Predictive Summary Table")
        overall_predictive_table = calculate_predictive_summary(df)
        st.write(overall_predictive_table)
        overall_manual_table = calculate_manual_summary(df)
        st.write(overall_manual_table)
