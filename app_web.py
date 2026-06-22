import os
import streamlit as streamlit
from google import genai
from dotenv import load_dotenv
from pypdf import PdfReader
import docx
from PIL import Image

# 1. Setup halaman web
streamlit.set_page_config(page_title="Super AI Vision & Doc Reader", page_icon="🧠")
streamlit.title("🧠 Adli AI: Pembaca Dokumen & Gambar")
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
        streamlit.success("Gambar berhasil dimuat!")
        
        # Kotak pertanyaan khusus gambar
        tanya_gambar = streamlit.text_input("Tanya sesuatu tentang gambar ini (Contoh: 'Jelaskan isi gambar ini' atau 'Terjemahkan teks di foto ini'):")
        if tanya_gambar:
            with streamlit.spinner("AI sedang menganalisis gambar..."):
                # Kirim teks pertanyaan DAN objek gambar sekaligus ke Gemini
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
            streamlit.success(f"Berhasil membaca dokumen: {nama_file}!")
            
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
