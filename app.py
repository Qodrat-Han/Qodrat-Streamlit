# app.py
import streamlit as st
import pickle
import pandas as pd
import google.generativeai as genai
import os
import time

# =====================================
# CONFIG DASAR
# =====================================
st.set_page_config(
    page_title="🚗 Prediksi Mobil + Chat AI",
    page_icon="🤖",
    layout="wide"
)

st.markdown(
    "<h1 style='text-align:center; color:#0d6efd;'>🚗 Prediksi Harga Mobil + Chat AI</h1>"
    "<p style='text-align:center; color:gray;'>Interaktif dengan AI — prediksi harga & konsultasi tanpa reload!</p>",
    unsafe_allow_html=True
)

# =====================================
# KONFIGURASI GEMINI (AUTO TANPA INPUT)
# =====================================
# Simpan API Key kamu di file .env atau environment sistem
# Contoh di terminal:
#    setx GEMINI_API_KEY "apikey_kamu"
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("⚠️ API Key Gemini belum ditemukan. Set environment variable `GEMINI_API_KEY` terlebih dahulu.")
else:
    genai.configure(api_key=api_key)

# =====================================
# SESSION STATE
# =====================================
for key in ["messages", "prediction_result", "last_car"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else ({} if key == "last_car" else None)

if "gemini_chat" not in st.session_state and api_key:
    try:
        st.session_state.gemini_chat = genai.GenerativeModel("models/gemini-2.5-flash").start_chat(history=[])
    except Exception as e:
        st.error(f"Gagal inisialisasi chat Gemini: {e}")

# =====================================
# LOAD MODEL PREDIKSI
# =====================================
@st.cache_resource
def load_model():
    with open("model.pkl", "rb") as f:
        return pickle.load(f)

try:
    model = load_model()
except Exception as e:
    st.error(f"Gagal memuat model.pkl: {e}")
    model = None

# =====================================
# SIDEBAR (HANYA INFO)
# =====================================
with st.sidebar:
    st.header("ℹ️ Informasi")
    if api_key:
        st.success("✅ Gemini API aktif")
    else:
        st.warning("⚠️ Gemini API belum diatur")

    st.markdown("---")
    st.caption("💬 Contoh pertanyaan:\n- Tips jual cepat?\n- Bandingkan model lain.\n- Mengapa harga mobil saya segitu?")

# =====================================
# FORM INPUT MOBIL
# =====================================
with st.expander("📋 Form Input Data Mobil", expanded=True):
    with st.form("prediksi_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            model_name = st.text_input("Model Mobil", "Audi A1")
            year = st.number_input("Tahun Produksi", 1990, 2025, 2017)
            transmission = st.selectbox("Transmisi", ["Manual", "Automatic", "Semi-Auto"])
        with col2:
            mileage = st.number_input("Jarak Tempuh (Mileage)", 0, 300000, 35000)
            fuelType = st.selectbox("Bahan Bakar", ["Petrol", "Diesel", "Hybrid", "Electric"])
            tax = st.number_input("Pajak (Tax)", 0, 1000, 30)
        with col3:
            mpg = st.number_input("Efisiensi (mpg)", 0.0, 200.0, 55.4)
            engineSize = st.number_input("Ukuran Mesin (engineSize)", 0.5, 6.0, 1.4)
            submit = st.form_submit_button("🔍 Prediksi Harga")

        if submit and model:
            try:
                df = pd.DataFrame([{
                    "model": model_name,
                    "year": year,
                    "transmission": transmission,
                    "mileage": mileage,
                    "fuelType": fuelType,
                    "tax": tax,
                    "mpg": mpg,
                    "engineSize": engineSize
                }])
                harga_pound = float(model.predict(df)[0])
                harga_rupiah = harga_pound * 19500

                st.session_state.last_car = {
                    "model": model_name,
                    "year": year,
                    "transmission": transmission,
                    "mileage": mileage,
                    "fuelType": fuelType,
                    "tax": tax,
                    "mpg": mpg,
                    "engineSize": engineSize,
                    "harga_rupiah": harga_rupiah,
                    "harga_pound": harga_pound
                }

                emoji = "💸" if harga_rupiah < 200_000_000 else "💰" if harga_rupiah < 500_000_000 else "🚀"
                hasil = f"{emoji} **Prediksi harga mobil:** Rp {harga_rupiah:,.0f} (≈ £{harga_pound:,.0f})"
                st.session_state.prediction_result = hasil
                st.success(hasil)

            except Exception as e:
                st.error(f"Gagal memprediksi: {e}")

# =====================================
# CHAT INTERAKTIF
# =====================================
st.markdown("---")
st.subheader("💬 Chat dengan AI")

chat_container = st.container()

def render_chat():
    with chat_container:
        for msg in st.session_state.messages:
            align = "right" if msg["role"] == "user" else "left"
            color = "#000000" if msg["role"] == "user" else "#0d6efd"
            st.markdown(f"""
                <div style='text-align:{align}; margin:5px 0;'>
                    <span style='background-color:{color}; color:white;
                                 padding:12px 15px; border-radius:15px;
                                 display:inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                                 max-width:80%; word-wrap:break-word;'>{msg['content']}</span>
                </div>
            """, unsafe_allow_html=True)

render_chat()

if prompt := st.chat_input("Tanyakan tentang mobil atau harga..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_chat()

    if not api_key:
        reply = "⚠️ Gemini belum aktif. Tambahkan API key di environment sistem."
    else:
        placeholder = st.empty()
        placeholder.markdown(f"<i style='color:gray;'>🤖 AI sedang mengetik...</i>", unsafe_allow_html=True)
        time.sleep(1.2)

        try:
            chat = st.session_state.gemini_chat
            context = f"""
Prediksi terakhir: {st.session_state.prediction_result or 'Belum ada prediksi.'}
Detail mobil: {st.session_state.last_car}
Instruksi: Jawab dengan ramah, jelas, dan relevan.
"""
            response = chat.send_message(f"{context}\nPengguna bertanya: {prompt}")
            reply = response.text
        except Exception as e:
            reply = f"⚠️ Terjadi kesalahan: {e}"

        st.session_state.messages.append({"role": "assistant", "content": reply})
        placeholder.empty()
        render_chat()
