import os
from pathlib import Path

def load_env(env_path: Path | None = None) -> dict[str, str]:
    """Tự động đọc các biến môi trường từ file .env.
    Ưu tiên tìm trong deepseek_bridge/.env, sau đó mới tìm ở thư mục gốc."""
    env_vars = {}
    if env_path is None:
        bridge_dir = Path(__file__).resolve().parent
        bridge_env = bridge_dir / ".env"
        root_env = bridge_dir.parent / ".env"
        
        if bridge_env.is_file():
            env_path = bridge_env
        elif root_env.is_file():
            env_path = root_env
        else:
            env_path = bridge_env  # Đường dẫn mặc định
    
    if env_path.is_file():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    env_vars[key] = val
                    if key not in os.environ:
                        os.environ[key] = val
    return env_vars

class DeepSeekConfig:
    def __init__(self):
        load_env()
        self.api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self.base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        # Cấu hình mặc định DeepSeek V4:
        # deepseek-v4-pro: bản Pro suy luận và phân tích sâu
        # deepseek-flash: bản V4.1-Flash siêu tốc, 1M context cho coding & thực thi
        self.model_reasoning = os.environ.get("DEEPSEEK_MODEL_REASONING", "deepseek-v4-pro")
        self.model_coding = os.environ.get("DEEPSEEK_MODEL_CODING", "deepseek-flash")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "your_deepseek_api_key_here")
