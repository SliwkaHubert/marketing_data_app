import streamlit as st
import pandas as pd
import plotly.express as px
import re
from datetime import datetime

# Funkcja do usuwania emotikonów
def remove_emoji(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emotikony twarzy
        "\U0001F300-\U0001F5FF"  # Symbole i piktogramy
        "\U0001F680-\U0001F6FF"  # Transport i symbole map
        "\U0001F1E0-\U0001F1FF"  # Flagi
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

# Funkcja do obliczania LTV na użytkownika
def calculate_ltv(df):
    # Zakładamy, że LTV = suma zakupów / liczba dni od pierwszego zakupu
    df['First_Purchase'] = df.groupby('user_id')['event_time'].transform('min')
    df['Days_Since_First_Purchase'] = (df['event_time'] - df['First_Purchase']).dt.days
    df['Days_Since_First_Purchase'] = df['Days_Since_First_Purchase'].replace(0, 1)  # Unikamy dzielenia przez zero
    df['LTV'] = df['price'] / df['Days_Since_First_Purchase']
    ltv_df = df.groupby('user_id').agg(
        Total_Revenue=('price', 'sum'),
        Total_Days=('Days_Since_First_Purchase', 'max'),
        LTV=('LTV', 'sum')
    ).reset_index()
    return ltv_df

# Funkcja do obliczania RFM
def calculate_rfm(df, reference_date):
    rfm_df = df.groupby('user_id').agg({
        'event_time': lambda x: (reference_date - x.max()).days,
        'user_id': 'count',
        'price': 'sum'
    }).rename(columns={
        'event_time': 'Recency',
        'user_id': 'Frequency',
        'price': 'Monetary'
    }).reset_index()
    return rfm_df

# Funkcja do segmentacji RFM
def rfm_segment(rfm):
    segments = []
    for _, row in rfm.iterrows():
        score = ''
        # Recency
        if row['Recency'] <= 30:
            score += '4'
        elif row['Recency'] <= 60:
            score += '3'
        elif row['Recency'] <= 90:
            score += '2'
        else:
            score += '1'
        # Frequency
        if row['Frequency'] >= 10:
            score += '4'
        elif row['Frequency'] >= 7:
            score += '3'
        elif row['Frequency'] >= 4:
            score += '2'
        else:
            score += '1'
        # Monetary
        if row['Monetary'] >= 1000:
            score += '4'
        elif row['Monetary'] >= 500:
            score += '3'
        elif row['Monetary'] >= 200:
            score += '2'
        else:
            score += '1'
        # Segmentacja na podstawie RFM Score
        if score == '444':
            segments.append('Champion')
        elif score.startswith('4') and score.endswith('3'):
            segments.append('Loyal Customer')
        elif score.startswith('3') and score.endswith('2'):
            segments.append('Potential Loyalist')
        elif score.startswith('2') and score.endswith('1'):
            segments.append('At Risk')
        else:
            segments.append('Others')
    rfm['Segment'] = segments
    return rfm

# Konfiguracja strony
st.set_page_config(page_title="📊 Dashboard - Analiza Danych", layout="wide")
st.title("📈 Dashboard - Analiza Danych")

# Sprawdzenie, czy plik został wgrany
if 'df_sales' not in st.session_state:
    st.warning("🚫 Proszę wgrać plik CSV na stronie głównej.")
    st.stop()

df_sales = st.session_state['df_sales']

try:
    # Konwersja event_time na datetime
    df_sales['event_time'] = pd.to_datetime(df_sales['event_time'])
except Exception as e:
    st.error(f"❌ Nie udało się przetworzyć kolumny 'event_time': {e}")
    st.stop()

# Wybór zakresu dat
min_date = df_sales['event_time'].min().date()
max_date = df_sales['event_time'].max().date()

start_date, end_date = st.date_input(
    "📅 Wybierz zakres dat",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

if start_date > end_date:
    st.error("❗ Data początkowa nie może być późniejsza niż data końcowa.")
else:
    # Filtrowanie danych po zakresie dat
    filtered_df = df_sales[(df_sales['event_time'].dt.date >= start_date) &
                           (df_sales['event_time'].dt.date <= end_date)]

    if filtered_df.empty:
        st.warning("⚠️ Brak danych dla wybranego zakresu dat.")
    else:
        # Obliczenia podstawowych metryk
        total_transactions = filtered_df.shape[0]
        total_revenue = filtered_df['price'].sum()
        average_transaction_value = filtered_df['price'].mean()
        unique_users = filtered_df['user_id'].nunique()
        average_transactions_per_user = total_transactions / unique_users if unique_users else 0
        ltv = total_revenue / unique_users if unique_users else 0

        # Wyświetlenie metryk w 3 kolumnach
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

        # Analiza zakupów wg godzin, dni tygodnia i miesięcy
        cart_data = filtered_df[filtered_df['event_type'] == 'purchase']

        if not cart_data.empty:
            cart_data['hour'] = cart_data['event_time'].dt.hour
            cart_data['day_of_week'] = cart_data['event_time'].dt.day_name()
            cart_data['month'] = cart_data['event_time'].dt.month_name()

            # Sortowanie dni tygodnia
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            cart_data['day_of_week'] = pd.Categorical(cart_data['day_of_week'], categories=day_order, ordered=True)

            # Sortowanie miesięcy chronologicznie
            month_order = ["January", "February", "March", "April", "May", "June",
                           "July", "August", "September", "October", "November", "December"]
            cart_data['month'] = pd.Categorical(cart_data['month'], categories=month_order, ordered=True)
            cart_data = cart_data.sort_values('month')

            # Suma wartości zakupów wg godzin (Plotly)
            hourly_revenue = cart_data.groupby('hour')['price'].sum().reset_index()
            fig_hourly = px.bar(hourly_revenue, x='hour', y='price',
                                labels={'hour': 'Godzina', 'price': 'Suma wartości zakupów'},
                                title="⏰ Suma wartości zakupów wg godzin",
                                color_discrete_sequence=["#636EFA"])
            st.plotly_chart(fig_hourly)

            # Suma wartości zakupów wg dni tygodnia (Plotly)
            daily_revenue = cart_data.groupby('day_of_week')['price'].sum().reset_index()
            fig_daily = px.bar(daily_revenue, x='day_of_week', y='price',
                               labels={'day_of_week': 'Dzień tygodnia', 'price': 'Suma wartości zakupów'},
                               title="📅 Suma wartości zakupów wg dni tygodnia",
                               color_discrete_sequence=["#EF553B"])
            st.plotly_chart(fig_daily)

            # Suma wartości zakupów wg miesięcy (Plotly)
            monthly_revenue = cart_data.groupby('month')['price'].sum().reset_index()
            fig_monthly = px.bar(monthly_revenue, x='month', y='price',
                                 labels={'month': 'Miesiąc', 'price': 'Suma wartości zakupów'},
                                 title="📆 Suma wartości zakupów wg miesięcy",
                                 color_discrete_sequence=["#00CC96"])
            st.plotly_chart(fig_monthly)
        else:
            st.info("ℹ️ Brak danych zakupowych w wybranym zakresie dat.")

        st.divider()

        # Sekcja Analiza LTV
        st.header("📊 Analiza Lifetime Value (LTV)")

        # Obliczenie LTV na użytkownika
        ltv_df = calculate_ltv(filtered_df)

        # Wyświetlenie podstawowych metryk LTV
        st.subheader("🔍 Podstawowe Metryki LTV")
        total_ltv = ltv_df['LTV'].sum()
        average_ltv = ltv_df['LTV'].mean()
        median_ltv = ltv_df['LTV'].median()
        st.metric("💎 Całkowity LTV wszystkich klientów", f"${total_ltv:,.2f}")
        st.metric("📈 Średni LTV na klienta", f"${average_ltv:,.2f}")
        st.metric("📊 Mediana LTV", f"${median_ltv:,.2f}")

        # Wizualizacja rozkładu LTV
        st.subheader("📉 Rozkład LTV klientów")
        fig_ltv = px.histogram(ltv_df, x='LTV', nbins=30,
                               labels={'LTV': 'Lifetime Value (LTV)'},
                               title="📈 Histogram LTV klientów",
                               color_discrete_sequence=["#AB63FA"])
        st.plotly_chart(fig_ltv)

        # Segmentacja LTV
        st.subheader("🔗 Segmentacja klientów na podstawie LTV")

        # Definiowanie progu segmentacji
        ltv_thresholds = st.slider("📊 Wybierz progi segmentacji LTV", min_value=float(ltv_df['LTV'].min()),
                                   max_value=float(ltv_df['LTV'].max()),
                                   value=(ltv_df['LTV'].quantile(0.25), ltv_df['LTV'].quantile(0.75)))

        low_threshold, high_threshold = ltv_thresholds

        def segment_ltv(ltv):
            if ltv >= high_threshold:
                return '💎 High LTV'
            elif ltv >= low_threshold:
                return '💰 Medium LTV'
            else:
                return '📉 Low LTV'

        ltv_df['LTV_Segment'] = ltv_df['LTV'].apply(segment_ltv)

        # Wyświetlenie liczby klientów w każdym segmencie
        segment_counts = ltv_df['LTV_Segment'].value_counts().reset_index()
        segment_counts.columns = ['LTV_Segment', 'Count']


        # Przeglądanie klientów w poszczególnych segmentach
        st.subheader("👥 Klienci w poszczególnych segmentach LTV")
        selected_segment = st.selectbox("📂 Wybierz segment LTV do wyświetlenia",
                                       options=segment_counts['LTV_Segment'].unique())
        segment_users = ltv_df[ltv_df['LTV_Segment'] == selected_segment]
        st.write(f"**{selected_segment}** - {segment_users.shape[0]} klientów")
        st.dataframe(segment_users[['user_id', 'Total_Revenue', 'Total_Days', 'LTV']].sort_values('LTV', ascending=False).reset_index(drop=True))

        st.divider()


        # Sekcja Pobierania Danych
        st.header("💾 Pobierz Wyniki Analizy")

        # Przygotowanie danych do pobrania
        # Kopiowanie DataFrame bez emotikonów w segmentacji
        ltv_no_emoji = ltv_df.copy()
        ltv_no_emoji['LTV_Segment'] = ltv_no_emoji['LTV_Segment'].apply(remove_emoji)

        # Możliwość pobrania LTV
        st.subheader("💎 Pobierz dane LTV klientów")
        csv_ltv = ltv_no_emoji.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="💾 Pobierz LTV jako CSV",
            data=csv_ltv,
            file_name='ltv_klientow.csv',
            mime='text/csv',
        )


