import streamlit as st
import pandas as pd
import plotly.express as px

st.title("📊 Aplikacja do analizy RFM")

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

    # Sekcja wyboru kolumn za pomocą serii checkboxów w Sidebarze
    with st.sidebar.expander("📋 Wybierz kolumny do wyświetlenia", expanded=False):
        all_columns = list(df_RFM.columns)  # Lista wszystkich kolumn RFM

        # Inicjalizacja session_state dla wybranych kolumn, jeśli nie istnieje
        if 'selected_columns_rfm' not in st.session_state:
            # Domyślne kolumny do wyświetlenia
            st.session_state['selected_columns_rfm'] = ["Recency", "Frequency", "Monetary"]

        selected_columns = st.session_state['selected_columns_rfm'].copy()  # Kopia wybranych kolumn

        # Tworzenie checkboxów dla każdej kolumny
        for col in all_columns:
            if st.checkbox(col, value=col in st.session_state['selected_columns_rfm']):
                if col not in selected_columns:
                    selected_columns.append(col)
            else:
                if col in selected_columns:
                    selected_columns.remove(col)

        # Aktualizacja session_state z wybranymi kolumnami
        st.session_state['selected_columns_rfm'] = selected_columns

    selected_columns = st.session_state['selected_columns_rfm']

    if selected_columns:
        # Wyświetlamy tabelę TYLKO z wybranymi kolumnami
        st.dataframe(df_RFM[selected_columns])
    else:
        st.info("⚠️ Wybierz przynajmniej jedną kolumnę do wyświetlenia.")

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
