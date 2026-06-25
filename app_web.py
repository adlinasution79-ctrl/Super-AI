import os
import streamlit as streamlit
from google import genai
from dotenv import load_dotenv
from pypdf import PdfReader
import docx
from PIL import Image

# 1. Setup halaman web
streamlit.set_page_config(page_title="Super AI Vision & Doc Reader", page_icon="🧠", layout="centered")

# Kustomisasi CSS Global agar tampilan tombol dan UI jauh lebih keren
streamlit.markdown("""
<style>
    /* Membuat efek gradien modern pada tombol utama */
    .stButton>button {
        background: linear-gradient(135deg, #00B4DB 0%, #0083B0 100%) !important;
        color: white !important;
        border: none !important;
        padding: 10px 24px !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 180, 219, 0.2) !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 180, 219, 0.4) !important;
        color: #f0f0f0 !important;
    }
    /* Mempercantik input teks */
    .stTextInput div div input {
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

streamlit.title("🧠 : Pembaca Dokumen & Gambar")
streamlit.write("Unggah file Dokumen (PDF/DOCX/TXT) ATAU Gambar (JPG/PNG), lalu ajukan pertanyaan Anda ke AI.")

# 2. Muat API Key dari .env
load_dotenv()
api_key_rahasia = os.getenv("GEMINI_API_KEY")

if "client" not in streamlit.session_state:
    streamlit.session_state.client = genai.Client(api_key=api_key_rahasia)

# Fungsi ekstraksi teks dokumen
def ekstrak_teks(file):
    nama_file = file.name
    if nama_file.endswith('.txt'):
        return file.read().decode("utf-8")
    elif nama_file.endswith('.pdf'):
        pembaca_pdf = PdfReader(file)
        return "".join([halaman.extract_text() or "" for halaman in pembaca_pdf.pages])
    elif nama_file.endswith('.docx'):
        dokumen_word = docx.Document(file)
        return "\n".join([p.text for p in dokumen_word.paragraphs])
    return None

# 3. Komponen Unggah File (Mendukung Dokumen & Gambar)
file_diunggah = streamlit.file_uploader(
    "Unggah dokumen Anda atau gambar di sini", 
    type=["txt", "pdf", "docx", "jpg", "jpeg", "png"]
)

if file_diunggah is not None:
    nama_file = file_diunggah.name
    
    # KONDISI A: JIKA YANG DIUNGGAH ADALAH GAMBAR
    if nama_file.lower().endswith(('.png', '.jpg', '.jpeg')):
        gambar = Image.open(file_diunggah)
        streamlit.image(gambar, caption="Pratinjau Gambar yang Diunggah", use_container_width=True)
        
        # Card Kustom HTML untuk Gambar (Menggunakan st.markdown agar aman)
        streamlit.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(46, 213, 115, 0.15) 0%, rgba(46, 213, 115, 0.05) 100%);
            border-left: 5px solid #2ed573;
            padding: 15px 20px;
            border-radius: 12px;
            margin: 15px 0;
            display: flex;
            align-items: center;
            box-shadow: 0 4px 12px rgba(46, 213, 115, 0.1);
        ">
            <span style="font-size: 20px; margin-right: 12px;">✅</span>
            <span style="color: #2ed573; font-weight: 600; font-family: sans-serif;">Gambar berhasil dimuat dan siap dianalisis!</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Kotak pertanyaan khusus gambar
        tanya_gambar = streamlit.text_input("Tanya sesuatu tentang gambar ini (Contoh: 'Jelaskan isi gambar ini' atau 'Terjemahkan teks di foto ini'):")
        if tanya_gambar:
            with streamlit.spinner("AI sedang menganalisis gambar..."):
                response = streamlit.session_state.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[tanya_gambar, gambar]
                )
                streamlit.markdown("### 🤖 Analisis AI:")
                streamlit.write(response.text)

    # KONDISI B: JIKA YANG DIUNGGAH ADALAH DOKUMEN
    else:
        isi_dokumen = ekstrak_teks(file_diunggah)
        if isi_dokumen:
            # Card Kustom HTML untuk Dokumen yang sudah diperbaiki variabelnya
            streamlit.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(0, 180, 219, 0.15) 0%, rgba(0, 131, 176, 0.05) 100%);
                border-left: 5px solid #00B4DB;
                padding: 15px 20px;
                border-radius: 12px;
                margin: 15px 0;
                display: flex;
                align-items: center;
                box-shadow: 0 4px 12px rgba(0, 180, 219, 0.1);
            ">
                <span style="font-size: 20px; margin-right: 12px;">📄</span>
                <span style="color: #00B4DB; font-weight: 600; font-family: sans-serif;">Berhasil membaca dokumen: {nama_file}!</span>
            </div>
            """, unsafe_allow_html=True)
            
            if streamlit.button("✨ Rangkum Otomatis"):
                with streamlit.spinner("AI sedang merangkum..."):
                    response = streamlit.session_state.client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"Rangkum dokumen ini secara padat:\n\n{isi_dokumen}"
                    )
                    streamlit.markdown("### 📝 Rangkuman AI:")
                    streamlit.write(response.text)
                    
            tanya_doc = streamlit.text_input("Tanya hal spesifik tentang isi dokumen ini:")
            if tanya_doc:
                with streamlit.spinner("AI sedang mencari jawaban..."):
                    response = streamlit.session_state.client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=f"Pertanyaan: {tanya_doc}\n\nDokumen:\n{isi_dokumen}"
                    )
                    streamlit.markdown("### 🤖 Jawaban AI:")
                    streamlit.write(response.text)
