import google.generativeai as genai
import os

# Masukkan API key kamu di sini
api_key = os.getenv("GEMINI_API_KEY") or "AIzaSyAvSmKtTjW5kHnmVsh9GEnJt_CPWsZfV40"

genai.configure(api_key=api_key)

# Menampilkan daftar model yang bisa dipakai
print("🔍 Daftar model Gemini yang tersedia untuk akun ini:\n")

for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(f"✅ {m.name}")

