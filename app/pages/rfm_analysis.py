import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Aplikacja do analizy RFM i więcej")


# Sprawdzenie, czy plik został wgrany
if 'df_sales' not in st.session_state:
    st.warning("🚫 **Proszę wgrać plik CSV na stronie głównej lub innej podstronie.**")
    st.stop()

df_sales = st.session_state['df_sales']

try:
    # Konwersja kolumny 'event_time' na datetime
    df_sales['event_time'] = pd.to_datetime(df_sales['event_time'])
except Exception as e:
    st.error(f"❌ Nie udało się przetworzyć kolumny 'event_time': {e}")
    st.stop()

# Wybór zakresu dat
min_date = df_sales['event_time'].min().date()
max_date = df_sales['event_time'].max().date()

st.sidebar.header("📅 Wybór Zakresu Dat")
start_date, end_date = st.sidebar.date_input(
    "📆 Wybierz zakres dat",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if start_date > end_date:
    st.error("❗ **Data początkowa nie może być późniejsza niż data końcowa.**")
    st.stop()

# Filtrowanie danych po zakresie dat
filtered_df = df_sales.loc[
    (df_sales['event_time'].dt.date >= start_date) &
    (df_sales['event_time'].dt.date <= end_date)
]

if filtered_df.empty:
    st.warning("⚠️ **Brak danych dla wybranego zakresu dat.**")
    st.stop()


total_transactions = filtered_df.shape[0]
total_revenue = filtered_df['price'].sum()
average_transaction_value = filtered_df['price'].mean()
unique_users = filtered_df['user_id'].nunique()
average_transactions_per_user = total_transactions / unique_users if unique_users else 0
ltv = total_revenue / unique_users if unique_users else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📦 Całkowita liczba transakcji", total_transactions)
    st.divider()
    st.metric("🛒 Średnia liczba zakupów na użytkownika", f"{average_transactions_per_user:.2f}")

with col2:
    st.metric("💰 Całkowita wartość transakcji", f"${total_revenue:,.2f}")
    st.divider()
    st.metric("🔄 Customer Lifetime Value (LTV)", f"${ltv:,.2f}")

with col3:
    st.metric("💵 Średnia wartość jednej transakcji", f"${average_transaction_value:,.2f}")
    st.divider()
    st.metric("👥 Liczba unikalnych użytkowników", unique_users)


cart_data = filtered_df[filtered_df['event_type'] == 'purchase']

if not cart_data.empty:
    cart_data['hour'] = cart_data['event_time'].dt.hour
    cart_data['day_of_week'] = cart_data['event_time'].dt.day_name()
    cart_data['month'] = cart_data['event_time'].dt.month_name()

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    cart_data['day_of_week'] = pd.Categorical(cart_data['day_of_week'], categories=day_order, ordered=True)

    month_order = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    cart_data['month'] = pd.Categorical(cart_data['month'], categories=month_order, ordered=True)

    hourly_revenue = cart_data.groupby('hour')['price'].sum().reset_index()
    fig_hourly = px.bar(hourly_revenue, x='hour', y='price',
                        labels={'hour': 'Godzina', 'price': 'Suma wartości zakupów'},
                        title="⏰ Suma wartości zakupów wg godzin",
                        color_discrete_sequence=["#636EFA"])
    st.plotly_chart(fig_hourly)

    daily_revenue = cart_data.groupby('day_of_week')['price'].sum().reset_index()
    fig_daily = px.bar(daily_revenue, x='day_of_week', y='price',
                       labels={'day_of_week': 'Dzień tygodnia', 'price': 'Suma wartości zakupów'},
                       title="📅 Suma wartości zakupów wg dni tygodnia",
                       color_discrete_sequence=["#EF553B"])
    st.plotly_chart(fig_daily)

    monthly_revenue = cart_data.groupby('month')['price'].sum().reset_index()
    monthly_revenue = monthly_revenue.sort_values('month')
    fig_monthly = px.bar(monthly_revenue, x='month', y='price',
                         labels={'month': 'Miesiąc', 'price': 'Suma wartości zakupów'},
                         title="📆 Suma wartości zakupów wg miesięcy",
                         color_discrete_sequence=["#00CC96"])
    st.plotly_chart(fig_monthly)
else:
    st.info("ℹ️ **Brak danych zakupowych w wybranym zakresie dat.**")


def compute_rfm(df_original: pd.DataFrame) -> pd.DataFrame:
    df_rfm = df_original.copy()

    # Recency
    df_rfm['Recency'] = (df_rfm["event_time"].max() - df_rfm["event_time"]).dt.days
    df_R = df_rfm.groupby('user_id')['Recency'].min().reset_index()
    df_F = df_rfm.groupby('user_id')['event_type'].count().reset_index().rename(columns={"event_type": "Frequency"})
    df_M = df_rfm.groupby('user_id')['price'].sum().reset_index().rename(columns={"price": "Monetary"})

    df_RF = pd.merge(df_R, df_F, on='user_id')
    df_RFM = pd.merge(df_RF, df_M, on='user_id')

    quantiles_R = df_RFM['Recency'].quantile([0.25, 0.50, 0.75]).to_dict()
    quantiles_F = df_RFM['Frequency'].quantile([0.25, 0.50, 0.75]).to_dict()
    quantiles_M = df_RFM['Monetary'].quantile([0.25, 0.50, 0.75]).to_dict()

    # Scoring Recency
    def recency_scoring(rfm):
        if rfm.Recency <= quantiles_R[0.25]:
            return 4
        elif rfm.Recency <= quantiles_R[0.50]:
            return 3
        elif rfm.Recency <= quantiles_R[0.75]:
            return 2
        else:
            return 1

    # Scoring Frequency
    def frequency_scoring(rfm):
        if rfm.Frequency >= quantiles_F[0.75]:
            return 4
        elif rfm.Frequency >= quantiles_F[0.50]:
            return 3
        elif rfm.Frequency >= quantiles_F[0.25]:
            return 2
        else:
            return 1

    # Scoring Monetary
    def monetary_scoring(rfm):
        if rfm.Monetary >= quantiles_M[0.75]:
            return 4
        elif rfm.Monetary >= quantiles_M[0.50]:
            return 3
        elif rfm.Monetary >= quantiles_M[0.25]:
            return 2
        else:
            return 1

    df_RFM['Recency_Score'] = df_RFM.apply(recency_scoring, axis=1)
    df_RFM['Frequency_Score'] = df_RFM.apply(frequency_scoring, axis=1)
    df_RFM['Monetary_Score'] = df_RFM.apply(monetary_scoring, axis=1)

    df_RFM['Customer_RFM_Score'] = (
        df_RFM['Recency_Score'].astype(str)
        + df_RFM['Frequency_Score'].astype(str)
        + df_RFM['Monetary_Score'].astype(str)
    )

    def categorizer(rfm):
        if (rfm[0] in ['2', '3', '4']) and (rfm[1] == '4') and (rfm[2] == '4'):
            return 'Champion'
        elif (rfm[0] == '3') and (rfm[1] in ['1', '2', '3', '4']) and (rfm[2] in ['3', '4']):
            return 'Top Loyal Customer'
        elif (rfm[0] == '3') and (rfm[1] in ['1', '2', '3', '4']) and (rfm[2] in ['1', '2']):
            return 'Loyal Customer'
        elif (rfm[0] == '4') and (rfm[1] in ['1', '2', '3', '4']) and (rfm[2] in ['3', '4']):
            return 'Top Recent Customer'
        elif (rfm[0] == '4') and (rfm[1] in ['1', '2', '3', '4']) and (rfm[2] in ['1', '2']):
            return 'Recent Customer'
        elif (rfm[0] in ['2', '3']) and (rfm[1] in ['1', '2', '3', '4']) and (rfm[2] in ['3', '4']):
            return 'Top Customer Needed Attention'
        elif (rfm[0] in ['2', '3']) and (rfm[1] in ['1', '2', '3', '4']) and (rfm[2] in ['1', '2']):
            return 'Customer Needed Attention'
        elif (rfm[0] == '1') and (rfm[1] in ['1', '2', '3', '4']) and (rfm[2] in ['3', '4']):
            return 'Top Lost Customer'
        elif (rfm[0] == '1') and (rfm[1] in ['1', '2', '3', '4']) and (rfm[2] in ['1', '2']):
            return 'Lost Customer'
        else:
            return 'Other'

    df_RFM['Customer_Category'] = df_RFM['Customer_RFM_Score'].apply(categorizer)

    return df_RFM


if st.button("🔍 Przeprowadź analizę RFM"):
    # Obliczamy RFM na przefiltrowanych danych (filtered_df)
    rfm_results = compute_rfm(filtered_df)
    st.session_state["df_rfm_results"] = rfm_results
    st.success("Analiza RFM została przeprowadzona pomyślnie!")

if "df_rfm_results" in st.session_state:
    df_RFM = st.session_state["df_rfm_results"].copy()

    # Usuwamy kolumnę 'user_id' z wyświetlania i pobierania
    if 'user_id' in df_RFM.columns:
        df_RFM = df_RFM.drop(columns=['user_id'])

    st.subheader("📈 Wyniki analizy RFM (wybrane kolumny):")
    # Wielokrotny wybór kolumn (multiselect)
    selected_columns = st.multiselect(
        "Wybierz kolumny:",
        df_RFM.columns.tolist(),
        default=["Recency", "Frequency", "Monetary"]
    )

    if selected_columns:
        # Wyświetlamy tabelę TYLKO z wybranymi kolumnami
        st.dataframe(df_RFM[selected_columns])
    else:
        st.info("Nie wybrano żadnych kolumn do wyświetlenia.")

    # Wizualizacja udziału kategorii
    st.subheader("📊 Wizualizacja segmentacji klientów:")
    size_rfm_label = df_RFM['Customer_Category'].value_counts().reset_index()
    size_rfm_label.columns = ['Customer_Category', 'Count']
    size_rfm_label['Percentage'] = (size_rfm_label['Count'] / size_rfm_label['Count'].sum()) * 100
    size_rfm_label['Label'] = (
        size_rfm_label['Customer_Category']
        + '<br>'
        + size_rfm_label['Percentage'].round(2).astype(str)
        + '%'
    )

    fig = px.treemap(
        size_rfm_label,
        path=['Label'],
        values='Count',
        title="📦 Segmentacja klientów (procentowy udział)",
        width=800, height=600
    )
    st.plotly_chart(fig)

    # Przygotowanie danych do KMeans
    if selected_columns:
        # Tworzymy kopię wybranych kolumn
        df_kmeans = df_RFM[selected_columns].copy()
    else:
        # Jeśli nie wybrano kolumn, zapisujemy cały DataFrame
        df_kmeans = df_RFM.copy()

    # Funkcja do zmiany pierwszej litery kolumny na małą literę
    def lowercase_first_letter(col_name):
        return col_name[0].lower() + col_name[1:] if isinstance(col_name, str) and len(col_name) > 0 else col_name

    # Zmieniamy nazwy kolumn
    df_kmeans.columns = [lowercase_first_letter(col) for col in df_kmeans.columns]

    # Zapisywanie do session_state dla KMeans
    st.session_state["df_kmeans"] = df_kmeans

    # Generujemy dane CSV z nagłówkami w małych literach
    csv_data = df_kmeans.to_csv(index=False, header=True, encoding='utf-8-sig').encode('utf-8-sig')

    st.download_button(
        label="💾 Pobierz wyniki RFM jako CSV",
        data=csv_data,
        file_name='wyniki_rfm.csv',
        mime='text/csv',
    )
