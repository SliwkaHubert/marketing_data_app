import streamlit as st
import joblib
import matplotlib.pyplot as plt
import plotly.express as px
import os
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
        data['Segment Name'] = labels.map(segment_labels)

        # Checkboxy dla wyboru segmentów
        unique_segments = sorted(data['Segment Name'].unique())
        selected_segments = st.multiselect(
            "Wybierz segmenty do wyświetlenia:",
            unique_segments,
            default=unique_segments
        )

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

        # Podświetlenie segmentu
        highlight_segment = st.selectbox(
            "Wybierz segment do podświetlenia na wykresie 3D:",
            options=["Wszystkie"] + list(segment_labels.values())
        )

        if highlight_segment != "Wszystkie":
            data['Highlight'] = data['Segment Name'].apply(
                lambda x: highlight_segment if x == highlight_segment else "Inne"
            )
            fig = px.scatter_3d(
                data,
                x='recency',
                y='frequency',
                z='monetary',
                color='Highlight',
                title=f"Wizualizacja klastrów (3D) - Podświetlenie: {highlight_segment}",
                color_discrete_map={
                    highlight_segment: color_map[highlight_segment],
                    "Inne": "lightgray"
                }
            )
        else:
            fig = px.scatter_3d(
                data,
                x='recency',
                y='frequency',
                z='monetary',
                color='Segment Name',
                title="Wizualizacja klastrów (3D - dynamiczna)",
                color_discrete_map=color_map
            )
        st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Błąd podczas dynamicznej wizualizacji klastrów 3D: {e}")

def summarize_clusters(data, labels_series, segment_labels):
    try:
        data['Segment'] = labels_series
        data['Segment Name'] = labels_series.map(segment_labels)

        # Szczegółowe podsumowanie klastrów
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

        st.subheader("📊 Podsumowanie klastrów")
        st.dataframe(summary)

        # Szczegóły klastrów
        st.subheader("👤 Szczegóły klientów w klastrze")
        selected_cluster = st.selectbox(
            "Wybierz klaster do wyświetlenia szczegółowych danych:",
            options=segment_labels.values()
        )
        detailed_data = data[data['Segment Name'] == selected_cluster]
        if not detailed_data.empty:
            st.write(f"Klienci w segmencie **{selected_cluster}**:")
            st.dataframe(detailed_data[['recency', 'frequency', 'monetary']])
            csv = detailed_data.to_csv(index=False)
            st.download_button(
                label=f"Pobierz dane segmentu {selected_cluster}",
                data=csv,
                file_name=f"segment_{selected_cluster}.csv",
                mime='text/csv'
            )
        else:
            st.info(f"Brak klientów w segmencie **{selected_cluster}**.")

        return summary
    except Exception as e:
        st.error(f"Błąd podczas podsumowania klastrów: {e}")
        return None

# Główna logika aplikacji
if "df_kmeans" not in st.session_state:
    st.warning("🚫 Brak danych do klasteryzacji KMeans.")
    st.stop()

df_kmeans = st.session_state["df_kmeans"].copy()

required_columns = ['recency', 'frequency', 'monetary']
if not all(col in df_kmeans.columns for col in required_columns):
    st.error("Dane nie zawierają wymaganych kolumn.")
    st.stop()

model_path = 'models/model_kmeans_cosmetic_05_org.joblib'
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found at {model_path}")

loaded_model = load_model(model_path)
if loaded_model is None:
    st.stop()

try:
    features = df_kmeans[required_columns]
    labels = loaded_model.predict(features)
    labels_series = pd.Series(labels, name="Segment")
    df_kmeans['Segment'] = labels_series

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

    # Dodanie filtrów na pasku bocznym
    st.sidebar.header("🔍 Filtry danych")

    # Filtr dla recency
    recency_range = st.sidebar.slider(
        "Zakres Recency:",
        min_value=float(df_kmeans['recency'].min()),
        max_value=float(df_kmeans['recency'].max()),
        value=(float(df_kmeans['recency'].min()), float(df_kmeans['recency'].max()))
    )

    # Filtr dla frequency
    frequency_range = st.sidebar.slider(
        "Zakres Frequency:",
        min_value=float(df_kmeans['frequency'].min()),
        max_value=float(df_kmeans['frequency'].max()),
        value=(float(df_kmeans['frequency'].min()), float(df_kmeans['frequency'].max()))
    )

    # Filtr dla monetary
    monetary_range = st.sidebar.slider(
        "Zakres Monetary:",
        min_value=float(df_kmeans['monetary'].min()),
        max_value=float(df_kmeans['monetary'].max()),
        value=(float(df_kmeans['monetary'].min()), float(df_kmeans['monetary'].max()))
    )

    # Filtrowanie danych na podstawie wybranych zakresów
    filtered_data = df_kmeans[
        (df_kmeans['recency'] >= recency_range[0]) & (df_kmeans['recency'] <= recency_range[1]) &
        (df_kmeans['frequency'] >= frequency_range[0]) & (df_kmeans['frequency'] <= frequency_range[1]) &
        (df_kmeans['monetary'] >= monetary_range[0]) & (df_kmeans['monetary'] <= monetary_range[1])
    ]

    # Wizualizacje
    st.subheader("Wizualizacja klastrów (2D - interaktywna)")
    visualize_clusters_2d_interactive(filtered_data, labels_series, color_map, segment_labels)

    st.subheader("Wizualizacja klastrów (3D - dynamiczna)")
    visualize_clusters_3d_dynamic(filtered_data, labels_series, color_map, segment_labels)

    st.subheader("📊 Podsumowanie i szczegóły")
    summarize_clusters(filtered_data, labels_series, segment_labels)

except Exception as e:
    st.error(f"Błąd podczas przetwarzania danych: {e}")
    st.stop()
