import streamlit as st
import pandas as pd
import io
import time

# Tytuł aplikacji
st.title("Marketingowa Analiza Danych")

# Opis aplikacji
st.write("""
    Witaj w aplikacji do analizy danych o zamówieniach! 
    Wgraj plik CSV poniżej, a następnie przejdź do odpowiednich analiz na innych stronach.
""")

# Funkcja do wgrywania pliku z dynamicznym paskiem postępu i wyróżnionymi komunikatami
def upload_file():
    uploaded_file = st.file_uploader("Wgraj plik CSV", type="csv")
    
    if uploaded_file is not None:
        # Placeholdery dla komunikatów i paska postępu
        progress_bar = st.empty()
        status_box = st.empty()

        # Etap 1: Plik został wybrany przez użytkownika
        status_box.info("📂 Plik został wybrany. Trwa weryfikacja...")
        progress = progress_bar.progress(0)  # Pasek postępu na 0%
        time.sleep(1)  # Symulacja krótkiego czasu na reakcję

        # Etap 2: Sprawdzenie rozmiaru pliku
        file_size_mb = uploaded_file.size / (1024 * 1024)
        progress.progress(10)  # Pasek postępu na 10%
        if file_size_mb > 1000:
            progress_bar.empty()  # Usunięcie paska postępu
            status_box.error(f"❌ Plik jest zbyt duży: {file_size_mb:.2f} MB. Maksymalny dozwolony rozmiar to 1000 MB.")
            return

        # Etap 3: Wgrywanie i przetwarzanie pliku
        status_box.warning("⚙️ Przetwarzanie pliku, proszę czekać...")
        time.sleep(1)  # Symulacja opóźnienia (opcjonalne)
        try:
            df = pd.read_csv(uploaded_file)
            progress.progress(66)  # Pasek postępu na 66%
            
            # Zapisanie danych w stanie sesji
            st.session_state['df_sales'] = df

            # Etap 4: Sukces
            status_box.success("✅ Plik został pomyślnie przetworzony!")
            progress.progress(100)  # Pasek postępu na 100%
            time.sleep(1)  # Daj czas na wyświetlenie 100%
            
            # Wyświetlenie danych i komunikat końcowy
            progress_bar.empty()  # Usunięcie paska postępu
            status_box.empty()  # Usunięcie ostatniego komunikatu, jeśli niepotrzebny
            st.success("🎉 Sukces! Plik został wgrany i przetworzony.")
            st.dataframe(df.head())
            st.balloons()

        except Exception as e:
            progress_bar.empty()  # Usunięcie paska postępu
            status_box.error(f"❌ Nie udało się wczytać pliku: {e}")

# Sprawdzenie, czy plik jest już wgrany
if 'df_sales' not in st.session_state:
    upload_file()
else:
    st.success("Plik CSV został już wgrany.")
    st.dataframe(st.session_state['df_sales'].head())
    if st.button("Wgraj inny plik"):
        del st.session_state['df_sales']
        upload_file()

st.divider()

# Funkcja do tworzenia szablonu CSV
def create_template():
    template_data = {
        "event_time": ["2019-12-14 12:23:30 UTC", "2019-12-25 06:08:52 UTC"],
        "event_type": ["purchase", "remove_from_cart"],
        "product_id": [5683541, 5873612],
        "category_id": [1487580005595612013, 1487580009496313889],
        "category_code": [None, None],
        "brand": [None, None],
        "price": [2.05, 5.56],
        "user_id": [556837580, 529021635],
        "user_session": [
            "cce598d8-2ea7-46cf-88e9-ffd212dcd3a5",
            "ebe94efa-741a-4ccc-8585-3c08a5d9c4ef",
        ],
    }
    return pd.DataFrame(template_data)

# Wyświetlenie tabeli z przykładem
template_df = create_template()

# Sekcja pobierania szablonu
st.header("Pobierz szablon pliku CSV")
csv_buffer = io.StringIO()
template_df.to_csv(csv_buffer, index=False)
st.download_button(
    label="Pobierz szablon CSV",
    data=csv_buffer.getvalue(),
    file_name="template.csv",
    mime="text/csv",
)

# Sekcja informacyjna o strukturze pliku
st.header("Wymagana struktura pliku CSV")
st.markdown(
    """
    Aby aplikacja działała poprawnie, plik CSV musi spełniać następujące wymagania:
    
    - **Format pliku**: CSV (Comma-Separated Values).
    - **Kodowanie**: UTF-8.
    - **Kolumny**:
        - `event_time` (data i czas zdarzenia, format: `YYYY-MM-DD HH:MM:SS UTC`).
        - `event_type` (typ zdarzenia - `purchase`).
        - `product_id` (unikalny identyfikator produktu).
        - `category_id` (unikalny identyfikator kategorii produktu).
        - `category_code` (kod kategorii produktu, może być pusty).
        - `brand` (marka produktu, może być pusta).
        - `price` (cena produktu jako liczba dziesiętna).
        - `user_id` (unikalny identyfikator użytkownika).
        - `user_session` (unikalny identyfikator sesji użytkownika - Opcjonalny).
        
    - **Przykładowy plik CSV**:
    """
)
st.dataframe(template_df)