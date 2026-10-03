import os
from pathlib import Path

def load_env(env_path: Path | None = None) -> dict[str, str]:
    """Tự động đọc các biến môi trường từ file .env nếu có mà không cần thư viện bên ngoài."""
    env_vars = {}
    if env_path is None:
        # Tìm .env ở thư mục gốc của dự án
        root_dir = Path(__file__).resolve().parent.parent
        env_path = root_dir / ".env"
    
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
        self.model_reasoning = os.environ.get("DEEPSEEK_MODEL_REASONING", "deepseek-reasoner")
        self.model_coding = os.environ.get("DEEPSEEK_MODEL_CODING", "deepseek-chat")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "your_deepseek_api_key_here")
