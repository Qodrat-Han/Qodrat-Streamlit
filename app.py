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
# GEMINI API
# =====================================
api_key = st.session_state.get("gemini_api_key") or os.getenv("GEMINI_API_KEY", "")
if api_key:
    genai.configure(api_key=api_key)

# =====================================
# SESSION STATE
# =====================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None

if "last_car" not in st.session_state:
    st.session_state.last_car = {}

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
# SIDEBAR
# =====================================
with st.sidebar:
    st.header("⚙️ Pengaturan")
    key_input = st.text_input("🔑 Gemini API Key", type="password", value=api_key)
    if st.button("Simpan API Key"):
        st.session_state.gemini_api_key = key_input
        os.environ["GEMINI_API_KEY"] = key_input
        st.success("✅ API Key disimpan!")
        # Inisialisasi ulang chat Gemini tanpa rerun
        try:
            st.session_state.gemini_chat = genai.GenerativeModel("models/gemini-2.5-flash").start_chat(history=[])
        except Exception as e:
            st.error(f"Gagal inisialisasi chat Gemini: {e}")

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

                # Simpan detail mobil di session_state
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

                # Emoji respons otomatis
                if harga_rupiah < 200_000_000:
                    emoji = "💸"
                elif harga_rupiah < 500_000_000:
                    emoji = "💰"
                else:
                    emoji = "🚀"
                hasil = f"{emoji} **Prediksi harga mobil:** Rp {harga_rupiah:,.0f} (≈ £{harga_pound:,.0f})"
                st.session_state.prediction_result = hasil
                st.success(hasil)

            except Exception as e:
                st.error(f"Gagal memprediksi: {e}")

# =====================================
# CHAT MODERN + TYPING ANIMATION
# =====================================
st.markdown("---")
st.subheader("💬 Chat dengan AI")

chat_container = st.container()

def render_chat():
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style='text-align:right; margin:5px 0;'>
                    <span style='background-color:#000000; color:white; 
                                 padding:12px 15px; border-radius:15px; 
                                 display:inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.3); 
                                 max-width:80%; word-wrap:break-word;'>{msg['content']}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='text-align:left; margin:5px 0;'>
                    <span style='background-color:#0d6efd; color:white; 
                                 padding:12px 15px; border-radius:15px; 
                                 display:inline-block; box-shadow: 0 2px 5px rgba(0,0,0,0.2); 
                                 max-width:80%; word-wrap:break-word;'>{msg['content']}</span>
                </div>
                """, unsafe_allow_html=True)

render_chat()

if prompt := st.chat_input("Tanyakan tentang mobil atau harga..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_chat()

    if not api_key:
        reply = "⚠️ Gemini belum aktif. Masukkan API key di sidebar."
    else:
        placeholder = st.empty()
        placeholder.markdown(f"<i style='color:gray;'>🤖 AI sedang mengetik...</i>", unsafe_allow_html=True)
        time.sleep(1.2)  # simulasi delay

        try:
            chat = st.session_state.gemini_chat
            context = f"""
Prediksi terakhir: {st.session_state.prediction_result or 'Belum ada prediksi.'}
Detail mobil: {st.session_state.last_car}
Instruksi: Jawab pertanyaan pengguna dengan ramah, jelas, dan informatif.
Berikan insight tambahan, tips, atau perbandingan jika relevan.
Jika harga mobil rendah, berikan tips meningkatkan nilai jual.
Jika harga tinggi, jelaskan faktor keunggulannya.
"""
            response = chat.send_message(f"{context}\nPengguna bertanya: {prompt}")
            reply = response.text
        except Exception as e:
            reply = f"⚠️ Terjadi kesalahan: {e}"

        st.session_state.messages.append({"role": "assistant", "content": reply})
        placeholder.empty()
        render_chat()

# =====================================
# AI PROAKTIF SETELAH PREDIKSI
# =====================================
if st.session_state.last_car and "gemini_chat" in st.session_state:
    try:
        car = st.session_state.last_car
        proactive_prompt = f"""
Mobil: {car['model']} ({car['year']}), {car['transmission']}, Mileage {car['mileage']}.
Harga prediksi: Rp {car['harga_rupiah']:,.0f}.
Berikan insight tambahan, tips, atau saran perawatan agar harga jual optimal.
"""
        proactive_reply = st.session_state.gemini_chat.send_message(proactive_prompt).text
        st.session_state.messages.append({"role": "assistant", "content": proactive_reply})
        render_chat()
    except Exception as e:
        st.warning(f"AI proaktif gagal: {e}")
