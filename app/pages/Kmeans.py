import streamlit as st
import joblib
import matplotlib.pyplot as plt
import plotly.express as px
import os

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
def visualize_clusters_2d(data, labels):
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        scatter = ax.scatter(data['recency'], data['frequency'], c=labels, cmap='viridis', alpha=0.7)
        legend1 = ax.legend(*scatter.legend_elements(), title="Segment")
        ax.add_artist(legend1)
        ax.set_xlabel("Recency")
        ax.set_ylabel("Frequency")
        ax.set_title("Wizualizacja klastrów (2D)")
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Błąd podczas wizualizacji klastrów 2D: {e}")

def visualize_clusters_3d_dynamic(data, labels):
    try:
        fig = px.scatter_3d(
            data,
            x='recency',
            y='frequency',
            z='monetary',
            color=labels.astype(str),
            title="Wizualizacja klastrów (3D - dynamiczna)",
            labels={'color': 'Segment'}
        )
        st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Błąd podczas dynamicznej wizualizacji klastrów 3D: {e}")

def summarize_clusters(data, labels):
    try:
        data['Segment'] = labels
        summary = data.groupby('Segment').agg(
            recency_mean=('recency', 'mean'),
            frequency_mean=('frequency', 'mean'),
            monetary_mean=('monetary', 'mean'),
            user_count=('Segment', 'count')
        ).reset_index()
        st.subheader("Podsumowanie klastrów")
        st.dataframe(summary)
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

# Predykcja klastrów
try:
    features = df_kmeans[required_columns]
    labels = loaded_model.predict(features)
    df_kmeans['Segment'] = labels
    st.write("**Dane z przypisanymi segmentami:**")
    st.dataframe(df_kmeans.head())
except Exception as e:
    st.error(f"Błąd podczas predykcji: {e}")
    st.stop()

# Wizualizacje
st.subheader("Wizualizacja klastrów (2D)")
visualize_clusters_2d(df_kmeans, labels)

st.subheader("Wizualizacja klastrów (3D - dynamiczna)")
visualize_clusters_3d_dynamic(df_kmeans, labels)

# Podsumowanie klastrów
summarize_clusters(df_kmeans, labels)
