import streamlit as st
import pandas as pd

# Tytuł aplikacji
st.title("Wielostronicowa Aplikacja Analizy Danych")

# Opis aplikacji
st.write("""
    Witaj w aplikacji do analizy danych! 
    Wgraj plik CSV poniżej, a następnie przejdź do odpowiednich analiz na innych stronach.
""")


# Funkcja do wgrywania pliku
def upload_file():
    uploaded_file = st.file_uploader("Wgraj plik CSV", type="csv")
    if uploaded_file is not None:
        # Sprawdzenie rozmiaru pliku w MB
        file_size_mb = uploaded_file.size / (1024 * 1024)
        if file_size_mb > 1000:
            st.error(f"Plik jest zbyt duży: {file_size_mb:.2f} MB. Maksymalny dozwolony rozmiar to 1000 MB.")
            return
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state['df_sales'] = df
            st.success("Plik został pomyślnie wgrany!")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Nie udało się wczytać pliku: {e}")


# Sprawdzenie, czy plik jest już wgrany
if 'df_sales' not in st.session_state:
    upload_file()
else:
    st.success("Plik CSV został już wgrany.")
    st.dataframe(st.session_state['df_sales'].head())
    if st.button("Wgraj inny plik"):
        del st.session_state['df_sales']
        upload_file()
