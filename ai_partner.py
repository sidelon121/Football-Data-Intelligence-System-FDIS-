import ollama
import sys
import os

# =================================================================
# KONFIGURASI FILTER (Agar AI tidak overload membaca file sampah)
# =================================================================
# Folder yang dilarang dibaca:
IGNORE_DIRS = ['venv', '__pycache__', '.git', 'temp_charts', 'sample_data'] 
# Tipe file yang boleh dibaca:
ALLOWED_EXTENSIONS = ['.py', '.html', '.css', '.js']

def baca_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[Error membaca file {file_path}: {e}]"

def kumpulkan_kode(target_path):
    gabungan_kode = ""
    
    # JIKA TARGET ADALAH FILE TUNGGAL
    if os.path.isfile(target_path):
        print(f"📂 Membaca file tunggal: {target_path}...")
        gabungan_kode += f"\n{'='*40}\nFILE: {target_path}\n{'='*40}\n"
        gabungan_kode += baca_file(target_path)
        
    # JIKA TARGET ADALAH FOLDER
    elif os.path.isdir(target_path):
        print(f"📁 Membaca isi folder: {target_path}...")
        for root, dirs, files in os.walk(target_path):
            # Membuang folder yang ada di daftar IGNORE_DIRS agar tidak ditelusuri
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                # Cek apakah file memiliki ekstensi yang diizinkan (misal .py)
                if any(file.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    print(f"   📄 Menambahkan: {file_path}")
                    gabungan_kode += f"\n{'='*40}\nFILE: {file_path}\n{'='*40}\n"
                    gabungan_kode += baca_file(file_path)
    else:
        return None
        
    return gabungan_kode

def diskusi_dengan_ai(target_path, prompt_user):
    # 1. Kumpulkan semua kode (baik dari 1 file atau 1 folder)
    kode_sumber = kumpulkan_kode(target_path)
    
    if not kode_sumber:
        print(f"❌ ERROR: Path '{target_path}' tidak ditemukan!")
        return

    # 2. Susun instruksi untuk AI
    full_prompt = f"""Anda adalah ahli software engineer dan full stack developer yang siap membantu saya.
    
Berikut adalah kode dari proyek saya:
{kode_sumber}

Pertanyaan/Instruksi saya:
{prompt_user}

Tolong berikan solusi yang tepat dan benar untuk semua masalah berdasarkan kode di atas."""

    print("\n⏳ Loading \n")
    
    # 3. Kirim ke Ollama
    try:
        response = ollama.chat(model='deepseek-coder-v2:16b', messages=[
            {
                'role': 'user',
                'content': full_prompt
            }
        ])
        
        print("==========================================")
        print(response['message']['content'])
        print("======================================================\n")
        
    except Exception as e:
        print(f"❌ Terjadi kesalahan saat memanggil Ollama: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("⚠️ Penggunaan yang benar:")
        print('python ai_partner.py <nama_file_atau_folder> "Pertanyaan Anda"')
        sys.exit(1)

    target_path = sys.argv[1]
    user_question = sys.argv[2]
    
    diskusi_dengan_ai(target_path, user_question)