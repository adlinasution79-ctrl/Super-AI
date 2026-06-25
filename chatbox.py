import os
from google import genai
from dotenv import load_dotenv

# 1. Mengambil API Key dari file .env secara otomatis
load_dotenv()
api_key_rahasia = os.getenv("GEMINI_API_KEY")

# 2. Menghubungkan ke server Google Gemini
client = genai.Client(api_key=api_key_rahasia)

# 3. Membuat sesi obrolan baru yang otomatis mengingat riwayat
chat = client.chats.create(model="gemini-2.5-flash")

print("=== CHATBOT PINTAR (DENGAN MEMORI) ===")
print("Ketik 'keluar' untuk mengakhiri obrolan.\n")

# 4. Memulai perulangan obrolan
while True:
    pesan_user = input("Anda: ")
    
    # Keluar dari program jika mengetik 'keluar'
    if pesan_user.lower() == 'keluar':
        print("Chatbot: Sampai jumpa!")
        break
        
    # Mengirim pesan ke AI di dalam sesi yang sama
    response = chat.send_message(pesan_user)
    # Menampilkan jawaban dari AI
    print(f"AI   : {response.text}\n")