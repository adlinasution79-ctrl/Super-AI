import os
import streamlit as streamlit
from google import genai
from dotenv import load_dotenv
from pypdf import PdfReader
import docx
from PIL import Image

# 1. Setup halaman web
streamlit.set_page_config(page_title="Super AI Vision & Doc Reader", page_icon="🧠", layout="centered")

# Kustomisasi CSS Global agar tampilan tombol, chat, dan UI jauh lebih keren & modern
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

    /* Menghilangkan sisa bayangan abu-abu luar pada container Streamlit */
    div[data-testid="stTextInputRootElement"] {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }
    .stTextInput > div {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* Kustomisasi kolom input teks utama */
    .stTextInput div div input {
        background-color: #202123 !important;
        color: #e2e8f0 !important;
        border: 1px solid #4d4d4f !important;
        border-radius: 28px !important;
        padding: 14px 24px !important;
        font-size: 16px !important;
        outline: none !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Efek visual saat kolom input diklik / aktif ketik */
    .stTextInput div div input:focus {
        border-color: #00B4DB !important;
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(0, 180, 219, 0.2) !important;
        background-color: #2a2b2d !important;
    }
    
    /* Menghilangkan label teks bawaan Streamlit di atas input agar terlihat bersih */
    .stTextInput label {
        display: none !important;
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

# --- MEMORI RIWAYAT CHAT (BARU) ---
if "riwayat_chat" not in streamlit.session_state:
    streamlit.session_state.riwayat_chat = []

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
        
        # Card Kustom HTML untuk Gambar
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
        
        # Tampilkan percakapan yang sudah berjalan sebelumnya
        for chat in streamlit.session_state.riwayat_chat:
            with streamlit.chat_message(chat["role"]):
                streamlit.markdown(chat["content"])

        # Kotak input pertanyaan baru
        tanya_gambar = streamlit.text_input(
            "Tanya Gambar", 
            placeholder="Ask anything about this image... (Contoh: Jelaskan isi gambar ini)",
            key="input_gambar"
        )
        
        if tanya_gambar:
            # Masukkan chat user ke dalam riwayat memori aplikasi
            streamlit.session_state.riwayat_chat.append({"role": "user", "content": tanya_gambar})
            with streamlit.chat_message("user"):
                streamlit.markdown(tanya_gambar)
                
            with streamlit.spinner("AI sedang berpikir..."):
                # Bangun seluruh riwayat pesan untuk dikirim ke Gemini agar AI paham konteks obrolan sebelumnya
                konteks_pesan = [
                    f"Konteks Gambar: Pengguna mengunggah sebuah gambar ke dalam sistem aplikasi."
                ]
                for c in streamlit.session_state.riwayat_chat[:-1]:
                    konteks_pesan.append(f"{c['role']}: {c['content']}")
                
                # Kirim semua riwayat teks chat + objek gambar utama ke model AI
                response = streamlit.session_state.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[*konteks_pesan, f"user: {tanya_gambar}", gambar]
                )
                
                # Masukkan respons AI ke memori dan tampilkan di layar
                streamlit.session_state.riwayat_chat.append({"role": "assistant", "content": response.text})
                with streamlit.chat_message("assistant"):
                    streamlit.markdown(response.text)
                    streamlit.rerun()

    # KONDISI B: JIKA YANG DIUNGGAH ADALAH DOKUMEN
    else:
        isi_dokumen = ekstrak_teks(file_diunggah)
        if isi_dokumen:
            # Card Kustom HTML untuk Dokumen
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
            
            # Tampilkan percakapan yang sudah berjalan sebelumnya
            for chat in streamlit.session_state.riwayat_chat:
                with streamlit.chat_message(chat["role"]):
                    streamlit.markdown(chat["content"])

            # Kotak input pertanyaan baru
            tanya_doc = streamlit.text_input(
                "Tanya Dokumen", 
                placeholder="Ask anything about this document... (Contoh: Apa kesimpulan file ini?)",
                key="input_doc"
            )
            
            if tanya_doc:
                # Masukkan chat user ke dalam riwayat memori aplikasi
                streamlit.session_state.riwayat_chat.append({"role": "user", "content": tanya_doc})
                with streamlit.chat_message("user"):
                    streamlit.markdown(tanya_doc)
                    
                with streamlit.spinner("AI sedang mencari jawaban..."):
                    # Bangun seluruh riwayat pesan untuk dikirim ke Gemini agar tahu konteks lama
                    konteks_pesan = [f"Isi Dokumen yang diunggah pengguna:\n{isi_dokumen}\n\n---\nRiwayat Percakapan:"]
                    for c in streamlit.session_state.riwayat_chat[:-1]:
                        konteks_pesan.append(f"{c['role']}: {c['content']}")
                    
                    response = streamlit.session_state.client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[*konteks_pesan, f"user: {tanya_doc}"]
                    )
                    
                    # Masukkan respons AI ke memori dan tampilkan di layar
                    streamlit.session_state.riwayat_chat.append({"role": "assistant", "content": response.text})
                    with streamlit.chat_message("assistant"):
                        streamlit.markdown(response.text)
