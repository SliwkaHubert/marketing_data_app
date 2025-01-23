import streamlit as st
import joblib
import matplotlib.pyplot as plt
import plotly.express as px
import os
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

st.title("🔢 Klasteryzacja KMeans")

# Funkcja do ładowania modelu
@st.cache_resource
def load_model(model_path):
    try:
        loaded_model = joblib.load(model_path)
        return loaded_model
    except Exception as e:
        st.error(f"Nie udało się załadować modelu: {e}")
        return None

# Funkcje do wizualizacji
def visualize_clusters_2d_interactive(data, labels, color_map, segment_labels):
    try:
        # Dodanie kolumny 'Segment Name' na podstawie przypisanych etykiet
        data['Segment Name'] = labels.map(segment_labels)

        # Checkboxy dla wybrania, które segmenty wyświetlić
        unique_segments = sorted(data['Segment Name'].unique())
        selected_segments = st.multiselect(
            "Wybierz segmenty do wyświetlenia:",
            unique_segments,
            default=unique_segments
        )

        # Filtracja danych na podstawie wyboru segmentów
        filtered_data = data[data['Segment Name'].isin(selected_segments)]

        # Wykres 2D
        fig, ax = plt.subplots(figsize=(10, 6))
        scatter = ax.scatter(
            filtered_data['recency'],
            filtered_data['frequency'],
            c=filtered_data['Segment Name'].map(color_map),
            alpha=0.7
        )
        legend1 = ax.legend(
            handles=scatter.legend_elements()[0],
            labels=selected_segments,
            title="Segment"
        )
        ax.add_artist(legend1)
        ax.set_xlabel("Recency")
        ax.set_ylabel("Frequency")
        ax.set_title("Wizualizacja klastrów (2D)")
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Błąd podczas dynamicznej wizualizacji klastrów 2D: {e}")

def visualize_clusters_3d_dynamic(data, labels, color_map, segment_labels):
    try:
        data['Segment Name'] = labels.map(segment_labels)
        fig = px.scatter_3d(
            data,
            x='recency',
            y='frequency',
            z='monetary',
            color='Segment Name',
            color_discrete_map=color_map,
            title="Wizualizacja klastrów (3D - dynamiczna)",
            labels={'color': 'Segment'}
        )
        st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Błąd podczas dynamicznej wizualizacji klastrów 3D: {e}")

def summarize_clusters(data, labels_series, segment_labels):
    try:
        # Dodanie kolumny z nazwami segmentów
        data['Segment'] = labels_series
        data['Segment Name'] = labels_series.map(segment_labels)

        # Podsumowanie danych w klastrach
        summary = data.groupby('Segment Name').agg(
            recency_mean=('recency', 'mean'),
            recency_std=('recency', 'std'),
            frequency_mean=('frequency', 'mean'),
            frequency_std=('frequency', 'std'),
            monetary_mean=('monetary', 'mean'),
            monetary_std=('monetary', 'std'),
            total_revenue=('monetary', 'sum'),
            user_count=('Segment', 'count')
        ).reset_index()

        # Dodanie procentowego udziału klastrów
        total_users = data['Segment'].count()
        total_revenue = data['monetary'].sum()
        summary['user_percentage'] = (summary['user_count'] / total_users) * 100
        summary['revenue_percentage'] = (summary['total_revenue'] / total_revenue) * 100

        # Wyświetlenie tabeli z podsumowaniem
        st.subheader("📊 Podsumowanie klastrów")
        st.dataframe(summary)

        # Wizualizacja udziału klientów w klastrach
        st.subheader("🧩 Procentowy udział klientów w klastrach")
        fig_users = px.pie(
            summary,
            names='Segment Name',
            values='user_percentage',
            title="Procentowy udział klientów w klastrach",
            color='Segment Name',
            color_discrete_map={
                "Champions": "green",
                "Loyal Customers": "blue",
                "At Risk": "orange",
                "Lost Customers": "red",
                "New Customers": "purple"
            }
        )
        st.plotly_chart(fig_users)

        # Wizualizacja udziału przychodów w klastrach
        st.subheader("💰 Udział przychodów w klastrach")
        fig_revenue = px.bar(
            summary,
            x='Segment Name',
            y='revenue_percentage',
            text='revenue_percentage',
            title="Procentowy udział przychodów w klastrach",
            labels={'revenue_percentage': 'Procent przychodów (%)'},
            color='Segment Name',
            color_discrete_map={
                "Champions": "green",
                "Loyal Customers": "blue",
                "At Risk": "orange",
                "Lost Customers": "red",
                "New Customers": "purple"
            }
        )
        fig_revenue.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        st.plotly_chart(fig_revenue)

        return summary
    except Exception as e:
        st.error(f"Błąd podczas podsumowania klastrów: {e}")
        return None

# Sprawdzenie, czy dane KMeans są dostępne w session_state
if "df_kmeans" not in st.session_state:
    st.warning("🚫 Brak danych do klasteryzacji KMeans. Przeprowadź analizę RFM najpierw na stronie 'Analiza RFM'.")
    st.stop()

df_kmeans = st.session_state["df_kmeans"].copy()

# Sprawdzenie, czy wymagane kolumny istnieją
required_columns = ['recency', 'frequency', 'monetary']
if not all(col in df_kmeans.columns for col in required_columns):
    st.error("Dane nie zawierają wymaganych kolumn: recency, frequency, monetary.")
    st.stop()

# Ładowanie modelu KMeans
model_path = 'models/model_kmeans_cosmetic_05_org.joblib'
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found at {model_path}")

loaded_model = load_model(model_path)

if loaded_model is None:
    st.stop()

try:
    # Przygotowanie danych bez skalowania
    features = df_kmeans[required_columns]

    # Predykcja klastrów
    labels = loaded_model.predict(features)

    # Konwersja labels na Pandas Series
    labels_series = pd.Series(labels, name="Segment")

    # Dodanie kolumny `Segment` do danych
    df_kmeans['Segment'] = labels_series

    # Zdefiniowanie segmentów i kolorów
    segment_labels = {
        0: "Champions",
        1: "Loyal Customers",
        2: "At Risk",
        3: "Lost Customers",
        4: "New Customers"
    }
    color_map = {
        "Champions": "green",
        "Loyal Customers": "blue",
        "At Risk": "orange",
        "Lost Customers": "red",
        "New Customers": "purple"
    }

    # Wizualizacje
    st.subheader("Wizualizacja klastrów (2D - interaktywna)")
    visualize_clusters_2d_interactive(df_kmeans, labels_series, color_map, segment_labels)

    st.subheader("Wizualizacja klastrów (3D - dynamiczna)")
    visualize_clusters_3d_dynamic(df_kmeans, labels_series, color_map, segment_labels)

    # Podsumowanie klastrów
    summarize_clusters(df_kmeans, labels_series, segment_labels)
except Exception as e:
    st.error(f"Błąd podczas przetwarzania danych: {e}")
    st.stop()
