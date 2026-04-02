import os
import argparse
import subprocess
import logging
from datetime import datetime
import tweepy
from dotenv import load_dotenv

# ==========================================
# KONFIGURASI LOGGING
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ==========================================
# KELAS UTAMA
# ==========================================
class SyncManager:
    def __init__(self):
        """Inisialisasi dan muat variabel lingkungan."""
        load_dotenv()
        self.file_log = "activity_log.md"
        self._authenticate_x()

    def _authenticate_x(self):
        """Autentikasi ke X API dengan aman menggunakan environment variables."""
        try:
            self.client = tweepy.Client(
                consumer_key=os.getenv("X_API_KEY"),
                consumer_secret=os.getenv("X_API_SECRET"),
                access_token=os.getenv("X_ACCESS_TOKEN"),
                access_token_secret=os.getenv("X_ACCESS_SECRET")
            )
        except Exception as e:
            logging.error(f"Gagal memuat kredensial X API. Pastikan file .env sudah diisi. Detail: {e}")
            exit(1)

    def post_to_x(self, message: str) -> str:
        """Memublikasikan status ke X (Twitter)."""
        try:
            logging.info("Mencoba mengirim pembaruan ke X...")
            response = self.client.create_tweet(text=message)
            tweet_id = response.data['id']
            logging.info(f"Berhasil! Tweet terpublikasi (ID: {tweet_id})")
            return tweet_id
        except tweepy.errors.TweepyException as e:
            logging.error(f"Gagal berinteraksi dengan X API: {e}")
            exit(1)

    def update_log_file(self, message: str):
        """Memperbarui file markdown lokal dengan log aktivitas baru."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Buat file jika belum ada, atau tambahkan (append) jika sudah ada
        with open(self.file_log, "a") as f:
            f.write(f"- **{timestamp}**: {message}\n")
        logging.info(f"File {self.file_log} berhasil diperbarui.")

    def git_commit_and_push(self, message: str):
        """Menjalankan perintah Git untuk stage, commit, dan push."""
        try:
            logging.info("Mempersiapkan Git commit...")
            
            # Git Add
            subprocess.run(["git", "add", self.file_log], check=True, capture_output=True)
            
            # Git Commit
            commit_msg = f"chore: sync activity - {message[:30]}..."
            subprocess.run(["git", "commit", "-m", commit_msg], check=True, capture_output=True)
            
            # Git Push
            logging.info("Melakukan push ke remote repository...")
            subprocess.run(["git", "push"], check=True, capture_output=True)
            
            logging.info("Selesai! Riwayat kontribusi Git Anda telah diperbarui (Hijau).")
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Operasi Git gagal. Pastikan Anda berada di dalam repositori Git yang valid. Detail: {e.stderr.decode('utf-8').strip()}")
            exit(1)

# ==========================================
# FUNGSI EKSEKUSI (CLI)
# ==========================================
def main():
    # Setup Argument Parser untuk input dari terminal
    parser = argparse.ArgumentParser(description="Alat CLI untuk memposting ke X dan otomatis update riwayat Git.")
    parser.add_argument(
        "-m", "--message", 
        type=str, 
        required=True, 
        help="Pesan status yang akan diposting ke X dan dijadikan log commit."
    )
    args = parser.parse_args()

    # Inisialisasi dan eksekusi alur kerja
    app = SyncManager()
    app.post_to_x(args.message)
    app.update_log_file(args.message)
    app.git_commit_and_push(args.message)

if __name__ == "__main__":
    main()