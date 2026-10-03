import argparse
import sys
from pathlib import Path

from .config import DeepSeekConfig
from .client import DeepSeekClient

def main():
    parser = argparse.ArgumentParser(
        description="DeepSeek Bridge CLI - Cầu nối điều phối giữa Antigravity và DeepSeek V4 cho dự án NCKH"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Kiểm tra cấu hình API Key và danh sách model khả dụng từ API"
    )
    parser.add_argument(
        "-t", "--task", type=str,
        help="Nội dung tác vụ cần DeepSeek thực hiện"
    )
    parser.add_argument(
        "-m", "--mode", choices=["reason", "code"], default="code",
        help="Chế độ chạy: 'reason' (suy luận sâu / brainstorm) hoặc 'code' (sinh mã nguồn)"
    )
    parser.add_argument(
        "-M", "--model", type=str, default=None,
        help="Chỉ định model cụ thể (VD: deepseek-v4-pro, deepseek-flash, deepseek-chat, deepseek-reasoner)"
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
            print(f"🧠 Default Reasoning Model: {config.model_reasoning}")
            print(f"💻 Default Coding Model: {config.model_coding}")
            
            client = DeepSeekClient(config)
            print("\n🔍 Đang kiểm tra danh sách model từ API endpoint...")
            models = client.list_models()
            if models:
                print("📋 Các model khả dụng trên tài khoản của bạn:")
                for m in models:
                    print(f"  - {m}")
            else:
                print("ℹ️ Không thể liệt kê model (hoặc endpoint /models không mở).")
        else:
            print("❌ Trạng thái: CHƯA CẤU HÌNH API KEY")
            print("Hướng dẫn: Tạo file .env tại thư mục deepseek_bridge/.env và thêm:")
            print("DEEPSEEK_API_KEY=sk-...")
            print("DEEPSEEK_MODEL_REASONING=deepseek-v4-pro")
            print("DEEPSEEK_MODEL_CODING=deepseek-flash")
        return

    if not args.task:
        print("Vui lòng cung cấp tác vụ thông qua --task hoặc dùng --check để kiểm tra cấu hình.")
        parser.print_help()
        sys.exit(1)

    client = DeepSeekClient(config)
    selected_model = args.model or (config.model_reasoning if args.mode == "reason" else config.model_coding)
    
    print(f"\n🚀 Đang gửi tác vụ tới DeepSeek...")
    print(f"🎯 Model: {selected_model} (Mode: {args.mode.upper()})")
    if args.files:
        print(f"📂 Đính kèm ngữ cảnh từ: {', '.join(args.files)}")

    try:
        if args.mode == "reason":
            res = client.brainstorm(task=args.task, relevant_files=args.files, model=args.model)
            if res.reasoning_content:
                print("\n" + "=" * 30 + f" [REASONING TRACE - {res.model}] " + "=" * 30)
                print(res.reasoning_content)
        else:
            res = client.generate_code(task=args.task, relevant_files=args.files, model=args.model)

        print("\n" + "=" * 30 + f" [KẾT QUẢ / MÃ NGUỒN - {res.model}] " + "=" * 30)
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
