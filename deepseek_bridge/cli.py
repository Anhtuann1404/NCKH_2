import argparse
import sys
from pathlib import Path

# Đảm bảo in tiếng Việt chuẩn trên Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from .config import DeepSeekConfig
from .client import DeepSeekClient
from .token_guard import TokenGuard
from .orchestrator import Orchestrator

def main():
    parser = argparse.ArgumentParser(
        description="DeepSeek Bridge CLI - Cầu nối điều phối giữa Antigravity và DeepSeek V4 cho dự án NCKH"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Kiểm tra cấu hình API Key và danh sách model khả dụng từ API"
    )
    parser.add_argument(
        "--token-stats", action="store_true",
        help="Xem thống kê lượng token đã sử dụng và hạn mức phiên"
    )
    parser.add_argument(
        "--reset-tokens", action="store_true",
        help="Đặt lại hạn mức phiên token"
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
        help="Chỉ định model cụ thể (VD: deepseek-v4-pro, deepseek-flash)"
    )
    parser.add_argument(
        "-O", "--orchestrate", action="store_true",
        help="Bật chế độ điều phối tự động: Nén ngữ cảnh -> Sinh code -> Kiểm định -> Tự sửa lỗi tối đa 3-4 lần"
    )
    parser.add_argument(
        "--max-retries", type=int, default=3,
        help="Số lần tự sửa lỗi tối đa trước khi dừng lại hỏi người dùng (mặc định: 3)"
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
    token_guard = TokenGuard()

    if args.token_stats:
        stats = token_guard.get_summary()
        curr = stats['currency']
        print("=== BÁO CÁO TÀI KHOẢN & SỐ DƯ DEEPSEEK API ===")
        print(f"💵 Số dư tài khoản hiện tại:   {stats['current_balance']:.2f} {curr}")
        print(f"📈 Mức nạp cao nhất ghi nhận: {stats['peak_balance']:.2f} {curr}")
        print(f"🔋 Tỷ lệ số dư khả dụng:       {stats['remaining_percentage']}%")
        print(f"🛑 Ngưỡng cảnh báo tự dừng:     {stats['stop_percentage_threshold']}% (khi chạm {stats['stop_balance_threshold']:.2f} {curr})")
        print("--------------------------------------------------")
        print(f"📊 Thống kê token đã dùng:     {stats['total_tokens_used']:,} tokens")
        print(f"   • Prompt tokens:            {stats['prompt_tokens_used']:,}")
        print(f"   • Completion tokens:        {stats['completion_tokens_used']:,}")
        print(f"   • Số lượt gọi API:          {stats['call_count']}")
        print(f"🔒 Giới hạn max/request:       {stats['max_tokens_per_call']:,} tokens")
        return

    if args.reset_tokens:
        token_guard.fetch_live_balance()
        print("✅ Đã đồng bộ số dư tài khoản trực tiếp từ API.")
        return

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
                
            stats = token_guard.get_summary()
            curr = stats['currency']
            print(f"\n💵 Số dư tài khoản: {stats['current_balance']:.2f} {curr} (Khả dụng: {stats['remaining_percentage']}%)")
            print(f"🛑 Hệ thống sẽ tự dừng khi số dư còn <= {stats['stop_percentage_threshold']}% ({stats['stop_balance_threshold']:.2f} {curr})")
        else:
            print("❌ Trạng thái: CHƯA CẤU HÌNH API KEY")
            print("Hướng dẫn: Tạo file .env tại thư mục deepseek_bridge/.env và thêm:")
            print("DEEPSEEK_API_KEY=sk-...")
        return

    if not args.task:
        print("Vui lòng cung cấp tác vụ thông qua --task hoặc dùng --check / --token-stats.")
        parser.print_help()
        sys.exit(1)

    # Chế độ 1: Điều phối tự động có vòng lặp kiểm định và giới hạn retry (Orchestrate)
    if args.orchestrate:
        orchestrator = Orchestrator(config)
        res = orchestrator.run_task(
            task=args.task,
            relevant_files=args.files,
            max_retries=args.max_retries,
            model=args.model,
            output_path=args.output
        )

        print("\n" + "=" * 30 + f" [KẾT QUẢ ĐIỀU PHỐI: {res.status}] " + "=" * 30)
        print(f"📌 Thông điệp: {res.message}")
        print(f"🔢 Số lần thử đã thực hiện: {res.attempts}/{res.max_retries}")
        
        if res.status == "SUCCESS":
            print("\n" + "=" * 25 + " [MÃ NGUỒN HOÀN CHỈNH ĐÃ KIỂM ĐỊNH] " + "=" * 25)
            print(res.code)
        elif res.status == "NEEDS_USER_DECISION":
            print("\n⚠️ CẦN QUYẾT ĐỊNH TỪ NGƯỜI DÙNG:")
            print("Các lỗi chưa thể tự khắc phục sau các lần thử:")
            for err in res.errors:
                print(f"  ❌ {err}")
            print("\n👉 Cậu có muốn mình tiếp tục yêu cầu DeepSeek sửa tiếp, hay cậu muốn mình trực tiếp can thiệp?")
        elif res.status == "TOKEN_LIMIT_EXCEEDED":
            print(f"\n🚨 {res.message}")
            print("Dùng `--reset-tokens` nếu bạn muốn khởi động phiên tính token mới.")

        return

    # Chế độ 2: Gọi trực tiếp một lần (Standard Client Call)
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
