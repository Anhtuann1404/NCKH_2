import argparse
import sys
from pathlib import Path

from .config import DeepSeekConfig
from .client import DeepSeekClient

def main():
    parser = argparse.ArgumentParser(
        description="DeepSeek Bridge CLI - Cầu nối điều phối giữa Antigravity và DeepSeek cho dự án NCKH"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Kiểm tra cấu hình API Key và trạng thái kết nối"
    )
    parser.add_argument(
        "-t", "--task", type=str,
        help="Nội dung tác vụ cần DeepSeek thực hiện"
    )
    parser.add_argument(
        "-m", "--mode", choices=["reason", "code"], default="code",
        help="Chế độ chạy: 'reason' (DeepSeek-R1 suy luận sâu) hoặc 'code' (DeepSeek-V3 sinh mã nguồn)"
    )
    parser.add_argument(
        "-f", "--files", nargs="*", default=[],
        help="Danh sách đường dẫn các file liên quan để nén ngữ cảnh gửi kèm"
    )
    parser.add_argument(
        "-o", "--output", type=str,
        help="Đường dẫn file để ghi kết quả (nếu không chỉ định, sẽ in ra màn hình)"
    )

    args = parser.parse_args()

    config = DeepSeekConfig()

    if args.check:
        print("=== KIỂM TRA CẤU HÌNH DEEPSEEK API ===")
        if config.is_configured:
            masked_key = config.api_key[:6] + "..." + config.api_key[-4:]
            print(f"✅ Trạng thái: ĐÃ CẤU HÌNH")
            print(f"🔑 API Key: {masked_key}")
            print(f"🌐 Base URL: {config.base_url}")
            print(f"🧠 Reasoning Model: {config.model_reasoning}")
            print(f"💻 Coding Model: {config.model_coding}")
        else:
            print("❌ Trạng thái: CHƯA CẤU HÌNH API KEY")
            print("Hướng dẫn: Tạo file .env tại thư mục deepseek_bridge/.env (hoặc thư mục gốc) và thêm:")
            print("DEEPSEEK_API_KEY=sk-...")
        return

    if not args.task:
        print("Vui lòng cung cấp tác vụ thông qua --task hoặc dùng --check để kiểm tra cấu hình.")
        parser.print_help()
        sys.exit(1)

    client = DeepSeekClient(config)
    
    print(f"\n🚀 Đang gửi tác vụ tới DeepSeek (Mode: {args.mode.upper()})...")
    if args.files:
        print(f"📂 Đính kèm ngữ cảnh từ: {', '.join(args.files)}")

    try:
        if args.mode == "reason":
            res = client.brainstorm(task=args.task, relevant_files=args.files)
            if res.reasoning_content:
                print("\n" + "=" * 30 + " [REASONING TRACE - DEEPSEEK-R1] " + "=" * 30)
                print(res.reasoning_content)
        else:
            res = client.generate_code(task=args.task, relevant_files=args.files)

        print("\n" + "=" * 30 + " [KẾT QUẢ / MÃ NGUỒN] " + "=" * 30)
        print(res.content)
        print(f"\n📊 Thống kê token: Prompt={res.prompt_tokens} | Completion={res.completion_tokens} | Total={res.total_tokens}")

        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(res.content)
            print(f"💾 Đã lưu kết quả vào: {out_path}")

    except Exception as e:
        print(f"\n❌ Lỗi thực thi: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
