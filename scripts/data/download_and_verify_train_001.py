import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

EXPECTED_BYTES = 322018201
EXPECTED_SHA256 = "260cb9c93299f6b244d48321fe115523159770f4e73446b382473628c6e81d74"
URL = "https://huggingface.co/datasets/phreshphish/phreshphish/resolve/eabec4b7a66324b79cc8a0ad856d1731dc26fe1a/data/train-001.parquet"

TARGET_DIR = Path("data/raw/phreshphish/data")
TARGET_FILE = TARGET_DIR / "train-001.parquet"
TEMP_FILE = TARGET_DIR / "train-001.parquet.tmp"


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(4 * 1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_with_resume(max_retries: int = 5):
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Bắt đầu tải shard train-001.parquet từ: {URL}")
    print(f"Dung lượng kỳ vọng: {EXPECTED_BYTES:,} bytes")
    print(f"Mã băm SHA-256 kỳ vọng: {EXPECTED_SHA256}")

    for attempt in range(1, max_retries + 1):
        existing_size = TEMP_FILE.stat().st_size if TEMP_FILE.exists() else 0
        if existing_size > EXPECTED_BYTES:
            print(f"Tệp tạm lớn hơn kích thước kỳ vọng ({existing_size:,} > {EXPECTED_BYTES:,}). Xóa và tải lại...")
            TEMP_FILE.unlink()
            existing_size = 0

        if existing_size == EXPECTED_BYTES:
            print(f"Tệp tạm đã đạt đủ kích thước {EXPECTED_BYTES:,} bytes. Bỏ qua tải và chuyển sang kiểm tra hash.")
            break

        headers = {"User-Agent": "NCKH_2-DataPipeline/1.0"}
        mode = "wb"
        if existing_size > 0:
            headers["Range"] = f"bytes={existing_size}-"
            mode = "ab"
            print(f"[Thử lần {attempt}] Tiếp tục tải (Resume) từ byte {existing_size:,} / {EXPECTED_BYTES:,}...")
        else:
            print(f"[Thử lần {attempt}] Bắt đầu tải mới từ byte 0...")

        req = urllib.request.Request(URL, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=90) as resp, open(TEMP_FILE, mode) as f_out:
                if resp.status not in (200, 206):
                    raise RuntimeError(f"HTTP Status bất thường: {resp.status}")

                chunk_size = 2 * 1024 * 1024  # 2 MB
                downloaded_in_session = 0
                last_print = time.time()
                start_time = time.time()

                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
                    downloaded_in_session += len(chunk)
                    total_current = existing_size + downloaded_in_session

                    now = time.time()
                    if now - last_print >= 5.0 or total_current >= EXPECTED_BYTES:
                        elapsed = now - start_time
                        speed = downloaded_in_session / elapsed / (1024 * 1024) if elapsed > 0 else 0
                        pct = (total_current / EXPECTED_BYTES) * 100
                        print(f"Đã tải: {total_current:,} / {EXPECTED_BYTES:,} bytes ({pct:.1f}%) - {speed:.2f} MB/s")
                        last_print = now

            # Nếu đến đây mà file đã đủ kích thước thì thoát vòng lặp retry
            current_size = TEMP_FILE.stat().st_size if TEMP_FILE.exists() else 0
            if current_size == EXPECTED_BYTES:
                break
            else:
                print(f"Cảnh báo: Luồng kết thúc nhưng kích thước mới đạt {current_size:,} / {EXPECTED_BYTES:,} bytes.")

        except Exception as err:
            current_size = TEMP_FILE.stat().st_size if TEMP_FILE.exists() else 0
            print(f"[Thử lần {attempt} gặp lỗi]: {err}. Đã tải được {current_size:,} bytes.", file=sys.stderr)
            if attempt == max_retries:
                raise
            time.sleep(3 * attempt)

    # Kiểm tra kích thước cuối cùng
    final_size = TEMP_FILE.stat().st_size if TEMP_FILE.exists() else 0
    if final_size != EXPECTED_BYTES:
        raise ValueError(f"LỖI DUNG LƯỢNG: Kích thước cuối cùng ({final_size:,}) khác kỳ vọng ({EXPECTED_BYTES:,})!")

    print("\n--- ĐANG TÍNH MÃ BĂM SHA-256 TOÀN BỘ TỆP ---")
    actual_sha = compute_sha256(TEMP_FILE)
    print(f"Mã băm SHA-256 tính toán: {actual_sha}")
    print(f"Mã băm SHA-256 kỳ vọng:   {EXPECTED_SHA256}")

    if actual_sha != EXPECTED_SHA256:
        TEMP_FILE.unlink()
        raise ValueError(f"LỖI TOÀN VẸN: SHA-256 ({actual_sha}) không khớp kỳ vọng ({EXPECTED_SHA256})! Đã xóa tệp hỏng.")

    if TARGET_FILE.exists():
        TARGET_FILE.unlink()
    TEMP_FILE.rename(TARGET_FILE)
    print(f"✅ ĐÃ XÁC MINH VÀ LƯU THÀNH CÔNG: {TARGET_FILE}")


if __name__ == "__main__":
    try:
        download_with_resume()
    except Exception as e:
        print(f"❌ THẤT BẠI: {e}", file=sys.stderr)
        sys.exit(1)
