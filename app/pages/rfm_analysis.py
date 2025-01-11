import streamlit as st
import pandas as pd
import plotly.express as px

# Tytuł aplikacji
st.title("Aplikacja do analizy RFM i więcej")
st.write("🔍 **Załaduj plik CSV**, a następnie kliknij przycisk, aby przeprowadzić analizę RFM.")

# Sprawdzenie, czy plik został wgrany
if 'df_sales' not in st.session_state:
    st.warning("🚫 **Proszę wgrać plik CSV na stronie głównej.**")
    st.stop()

df_sales = st.session_state['df_sales']

# Uploader pliku (opcjonalny, jeśli chcesz umożliwić ponowne wgrywanie na tej samej stronie)
# Jeśli używasz struktury wielostronicowej, usuń ten fragment z tej strony
# uploaded_file = st.file_uploader("📂 Wgraj plik CSV", type="csv")
# if uploaded_file is not None:
#     try:
#         df = pd.read_csv(uploaded_file)
#         df['user_id'] = df['user_id'].astype(str)
#         df['event_time'] = pd.to_datetime(df['event_time'])
#         st.session_state['df_sales'] = df
#         st.success("✅ Plik został pomyślnie wgrany!")
#         st.dataframe(df.head())
#     except Exception as e:
#         st.error(f"❌ Nie udało się wczytać pliku: {e}")

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
else:
    # Filtrowanie danych po zakresie dat
    filtered_df = df_sales[(df_sales['event_time'].dt.date >= start_date) &
                           (df_sales['event_time'].dt.date <= end_date)]

    if filtered_df.empty:
        st.warning("⚠️ **Brak danych dla wybranego zakresu dat.**")
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
            monthly_revenue = monthly_revenue.sort_values('month')

            fig_monthly = px.bar(monthly_revenue, x='month', y='price',
                                 labels={'month': 'Miesiąc', 'price': 'Suma wartości zakupów'},
                                 title="📆 Suma wartości zakupów wg miesięcy",
                                 color_discrete_sequence=["#00CC96"])
            st.plotly_chart(fig_monthly)
        else:
            st.info("ℹ️ **Brak danych zakupowych w wybranym zakresie dat.**")

        # Przycisk do przeprowadzenia analizy RFM
        if st.button("🔍 Przeprowadź analizę RFM"):
            # Obliczenie Recency, Frequency i Monetary
            df_sales['Recency'] = (df_sales["event_time"].max() - df_sales["event_time"]).dt.days
            df_R = df_sales.groupby('user_id')['Recency'].min().reset_index().rename(columns={"Recency": "Recency"})
            df_F = df_sales.groupby('user_id')['event_type'].count().reset_index().rename(columns={"event_type": "Frequency"})
            df_M = df_sales.groupby('user_id')['price'].sum().reset_index().rename(columns={"price": "Monetary"})

            # Połączenie danych w jeden DataFrame
            df_RF = pd.merge(df_R, df_F, on='user_id')
            df_RFM = pd.merge(df_RF, df_M, on='user_id')

            # Obliczenie kwantyli jako skalarów
            quantiles_R = df_RFM['Recency'].quantile([0.25, 0.50, 0.75]).to_dict()
            quantiles_F = df_RFM['Frequency'].quantile([0.25, 0.50, 0.75]).to_dict()
            quantiles_M = df_RFM['Monetary'].quantile([0.25, 0.50, 0.75]).to_dict()

            # Funkcje do scoringu RFM
            def recency_scoring(rfm):
                if rfm.Recency <= quantiles_R[0.25]:
                    return 4
                elif rfm.Recency <= quantiles_R[0.50]:
                    return 3
                elif rfm.Recency <= quantiles_R[0.75]:
                    return 2
                else:
                    return 1

            def frequency_scoring(rfm):
                if rfm.Frequency >= quantiles_F[0.75]:
                    return 4
                elif rfm.Frequency >= quantiles_F[0.50]:
                    return 3
                elif rfm.Frequency >= quantiles_F[0.25]:
                    return 2
                else:
                    return 1

            def monetary_scoring(rfm):
                if rfm.Monetary >= quantiles_M[0.75]:
                    return 4
                elif rfm.Monetary >= quantiles_M[0.50]:
                    return 3
                elif rfm.Monetary >= quantiles_M[0.25]:
                    return 2
                else:
                    return 1

            # Dodanie kolumn scoringowych
            df_RFM['Recency_Score'] = df_RFM.apply(recency_scoring, axis=1)
            df_RFM['Frequency_Score'] = df_RFM.apply(frequency_scoring, axis=1)
            df_RFM['Monetary_Score'] = df_RFM.apply(monetary_scoring, axis=1)

            # Tworzenie ogólnego RFM Score
            df_RFM['Customer_RFM_Score'] = df_RFM['Recency_Score'].astype(str) + df_RFM['Frequency_Score'].astype(str) + df_RFM['Monetary_Score'].astype(str)

            # Funkcja do kategoryzacji klientów
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

            # Dodanie kolumny z kategorią klienta
            df_RFM['Customer_Category'] = df_RFM['Customer_RFM_Score'].apply(categorizer)

            # Wyświetlenie wyników
            st.subheader("📈 Wyniki analizy RFM:")
            st.dataframe(df_RFM)

            # Obliczanie ilości użytkowników i procentowego udziału
            Size_RFM_Label = df_RFM['Customer_Category'].value_counts()
            Size_RFM_Label_df = pd.DataFrame(Size_RFM_Label).reset_index()
            Size_RFM_Label_df.columns = ['Customer_Category', 'Count']
            Size_RFM_Label_df['Percentage'] = (Size_RFM_Label_df['Count'] / Size_RFM_Label_df['Count'].sum()) * 100
            Size_RFM_Label_df['Label'] = Size_RFM_Label_df['Customer_Category'] + \
                '<br>' + Size_RFM_Label_df['Percentage'].round(2).astype(str) + '%'

            # Wizualizacja za pomocą Plotly
            st.subheader("📊 Wizualizacja segmentacji klientów:")
            fig = px.treemap(
                Size_RFM_Label_df,
                path=['Label'],  # Wyświetlenie nazwy grupy z procentami
                values='Count',
                title="📦 Segmentacja klientów (procentowy udział)",
                width=800, height=600
            )
            st.plotly_chart(fig)

            # Możliwość zapisania wyników
            csv = df_RFM.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="💾 Pobierz wyniki RFM jako CSV",
                data=csv,
                file_name='wyniki_rfm.csv',
                mime='text/csv',
            )
        st.divider()
