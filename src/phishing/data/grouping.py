"""Module phân nhóm tên miền và nhận diện hạ tầng dùng chung (UGC / Multi-tenant).

Nguyên tắc ARS (Academic Research Skills) & Ponytail Discipline:
1. Dùng eTLD+1 với Public Suffix List (PSL) khóa cục bộ, hoàn toàn offline (Zero Network Calls).
2. Xử lý hạ tầng dùng chung (SharePoint, Google Sites, Office Forms, S3, Azure Blob, Firebase...)
   theo ranh giới tenant để tránh gom toàn bộ Internet vào một nhóm hoặc chia lẻ sai bản chất.
3. Nếu không xác định được tenant đáng tin cậy trên dịch vụ dùng chung, áp dụng quy tắc gom nhóm
   bảo thủ (conservative grouping) để bảo đảm an toàn chống rò rỉ dữ liệu.
4. Kết quả trả về group_id chuẩn hóa dạng chuỗi định danh bất biến (deterministic).
"""

from typing import Optional
from urllib.parse import parse_qs, urlsplit
import ipaddress
import re
import tldextract

# Khởi tạo extractor offline với danh mục PSL tích hợp sẵn của thư viện.
# suffix_list_urls=None bảo đảm tuyệt đối không gọi HTTP ra Internet trong quá trình chạy.
# include_psl_private_domains=True tự động bóc tách các private suffix phổ biến
# (như *.github.io, *.blob.core.windows.net, *.s3.amazonaws.com, *.pages.dev, *.web.app, *.vercel.app...).
_EXTRACTOR = tldextract.TLDExtract(
    suffix_list_urls=None,
    include_psl_private_domains=True,
    extra_suffixes=[],
)


def extract_group_id(url: str) -> str:
    """Trích xuất mã định danh nhóm (group_id) từ URL để phục vụ phân chia Grouped CV.

    Quy tắc phân định:
    - IP addresses (IPv4/IPv6): ip:<address>
    - SharePoint: tenant:<tenant>.sharepoint.com
    - Google Sites: tenant:sites.google.com/view/<name> hoặc tenant:sites.google.com/site/<name>
    - Office Forms: tenant:forms.office.com:id=<form_id> hoặc tenant:forms.office.com:r=<code>
    - S3 path-style: tenant:s3:<bucket>
    - Tên miền thông thường (kèm PSL private domains): domain:<eTLD+1>
    - Fallback: host:<hostname> hoặc "unknown" nếu URL không hợp lệ.
    """
    if not isinstance(url, str):
        raise TypeError(f"URL must be a string, got {type(url).__name__}")

    raw_url = url.strip()
    if not raw_url:
        return "unknown"

    # Đảm bảo có scheme để urlsplit bóc tách hostname chính xác
    if "://" not in raw_url:
        parsed = urlsplit(f"http://{raw_url}")
    else:
        parsed = urlsplit(raw_url)

    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        return "unknown"

    path = parsed.path or ""

    # 1. Kiểm tra địa chỉ IP thuần (IPv4 / IPv6)
    try:
        ip = ipaddress.ip_address(host)
        return f"ip:{ip}"
    except ValueError:
        pass

    # 2. Xử lý Microsoft SharePoint (subdomain là tenant riêng biệt)
    if host.endswith(".sharepoint.com"):
        tenant = host[:-len(".sharepoint.com")]
        if tenant:
            return f"tenant:{tenant}.sharepoint.com"
        return "domain:sharepoint.com"

    # 3. Xử lý Google Sites (sites.google.com/view/<site_id> hoặc /site/<site_id>)
    if host == "sites.google.com":
        path_clean = path.strip("/")
        segments = [seg for seg in path_clean.split("/") if seg]
        if len(segments) >= 2 and segments[0] in ("view", "site"):
            return f"tenant:sites.google.com/{segments[0]}/{segments[1].lower()}"
        if len(segments) >= 1 and segments[0]:
            return f"tenant:sites.google.com/{segments[0].lower()}"
        return "domain:sites.google.com"

    # 4. Xử lý Microsoft Forms (forms.office.com / forms.microsoft.com)
    if host in ("forms.office.com", "forms.microsoft.com"):
        qs = parse_qs(parsed.query)
        if "id" in qs and qs["id"] and qs["id"][0].strip():
            form_id = qs["id"][0].strip().lower()
            return f"tenant:{host}:id={form_id}"
        path_clean = path.strip("/")
        if path_clean.startswith("r/"):
            parts = path_clean.split("/")
            if len(parts) >= 2 and parts[1]:
                return f"tenant:{host}:r={parts[1].lower()}"
        return f"domain:{host}"

    # 5. Xử lý S3 path-style (s3.amazonaws.com/<bucket>/...)
    if host in ("s3.amazonaws.com", "s3.us-east-1.amazonaws.com") or (
        host.startswith("s3.") and host.endswith(".amazonaws.com")
    ):
        path_clean = path.strip("/")
        segments = [seg for seg in path_clean.split("/") if seg]
        if segments and segments[0]:
            return f"tenant:s3:{segments[0].lower()}"
        return "domain:s3.amazonaws.com"

    # 6. Trích xuất eTLD+1 qua tldextract (đã bao gồm PSL private domains)
    extracted = _EXTRACTOR(host)
    if extracted.ipv4 or extracted.ipv6:
        return f"ip:{extracted.ipv4 or extracted.ipv6}"

    if extracted.domain and extracted.suffix:
        return f"domain:{extracted.domain}.{extracted.suffix}".lower()

    if extracted.domain:
        return f"host:{extracted.domain}".lower()

    return f"host:{host}".lower()
