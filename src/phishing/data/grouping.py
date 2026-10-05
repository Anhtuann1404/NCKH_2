"""Module phân nhóm tên miền và nhận diện hạ tầng dùng chung (UGC / Multi-tenant).

Nguyên tắc ARS (Academic Research Skills) & Ponytail Discipline:
1. Dùng eTLD+1 với Public Suffix List (PSL) khóa cục bộ, hoàn toàn offline (Zero Network Calls).
2. Xử lý hạ tầng dùng chung (SharePoint, Google Sites, Office Forms, S3, Azure Blob, Firebase...)
   theo ranh giới tenant để tránh gom toàn bộ Internet vào một nhóm hoặc chia lẻ sai bản chất.
3. Chuẩn hóa các điểm cuối AWS S3 (cả path-style và virtual-hosted-style qua mọi region/dualstack)
   về cùng một khóa bucket tenant duy nhất (tenant:s3:<bucket>). Alias chưa xác minh xử lý bảo thủ.
4. Nếu không xác định được tenant đáng tin cậy trên dịch vụ dùng chung, áp dụng quy tắc gom nhóm
   bảo thủ (conservative grouping) để bảo đảm an toàn chống rò rỉ dữ liệu.
5. Kết quả trả về group_id chuẩn hóa dạng chuỗi định danh bất biến (deterministic).
"""

from typing import Optional
import hashlib
import ipaddress
import os
import re
from urllib.parse import parse_qs, urlsplit
import tldextract

from phishing.preprocessing.urls import normalize_hostname

GROUP_RULES_VERSION = "1.1.0"
TLDEXTRACT_VERSION = getattr(tldextract, "__version__", "bundled")


def _load_psl_snapshot_and_sha256() -> tuple[bytes, str]:
    """Tải snapshot PSL tích hợp trong tldextract và tính mã băm SHA-256 từ dữ liệu thực dùng.

    ARS CONTRACT: Không dùng fallback hash viết cứng; dừng ngay lập tức nếu snapshot bị thiếu.
    """
    import pkgutil
    data = pkgutil.get_data("tldextract", ".tld_set_snapshot")
    if data is None:
        pkg_dir = os.path.dirname(tldextract.__file__)
        snapshot_path = os.path.join(pkg_dir, ".tld_set_snapshot")
        if os.path.exists(snapshot_path):
            with open(snapshot_path, "rb") as f:
                data = f.read()

    if data is None:
        raise RuntimeError(
            "LỖI TOÀN VẸN PSL: Không thể đọc tệp snapshot '.tld_set_snapshot' từ tldextract. "
            "Anti-leakage protocol bắt buộc phải có snapshot PSL cục bộ hợp lệ để định danh nhóm."
        )

    return data, hashlib.sha256(data).hexdigest()


_PSL_BYTES, PSL_SNAPSHOT_SHA256 = _load_psl_snapshot_and_sha256()
PSL_VERSION = PSL_SNAPSHOT_SHA256

# Khởi tạo extractor offline với snapshot cố định, cache_dir=None để triệt tiêu việc đọc/ghi cache ngoài luồng.
# suffix_list_urls=None bảo đảm tuyệt đối không gọi HTTP ra Internet trong quá trình chạy.
# include_psl_private_domains=True tự động bóc tách các private suffix phổ biến
_EXTRACTOR = tldextract.TLDExtract(
    cache_dir=None,
    suffix_list_urls=None,
    fallback_to_snapshot=True,
    include_psl_private_domains=True,
    extra_suffixes=[],
)

# Regex chuẩn hóa các điểm cuối Amazon S3 chính thức theo tài liệu AWS:
# 1. Path-style: s3.amazonaws.com, s3.us-west-2.amazonaws.com, s3-us-west-2.amazonaws.com, s3.dualstack...
S3_PATH_STYLE_RE = re.compile(
    r"^s3(?:[-.](?:dualstack\.|fips\.)?[a-z0-9-]+)?\.amazonaws\.com$",
    re.IGNORECASE,
)
# 2. Virtual-hosted style: <bucket>.s3.amazonaws.com, <bucket>.s3.us-west-2.amazonaws.com, <bucket>.s3-website...
S3_VIRTUAL_HOST_RE = re.compile(
    r"^([a-z0-9][a-z0-9.-]+?)\.s3(?:[-.](?:dualstack\.|fips\.|website[-.]?)?[a-z0-9-]+)?\.amazonaws\.com$",
    re.IGNORECASE,
)


def extract_group_id(url: str) -> str:
    """Trích xuất mã định danh nhóm (group_id) từ URL để phục vụ phân chia Grouped CV.

    Quy tắc phân định:
    - IP addresses (IPv4/IPv6): ip:<address>
    - SharePoint: tenant:<tenant>.sharepoint.com
    - Google Sites: tenant:sites.google.com/view/<name> hoặc tenant:sites.google.com/site/<name>
    - Office Forms: tenant:forms.office.com:id=<form_id> hoặc tenant:forms.office.com:r=<code>
    - AWS S3 (chuẩn hóa cả path-style & virtual-hosted): tenant:s3:<bucket>
    - Tên miền thông thường (kèm PSL private domains): domain:<eTLD+1>
    - Fallback: host:<hostname> hoặc "unknown" nếu URL/hostname không hợp lệ.
    """
    if not isinstance(url, str):
        raise TypeError(f"URL must be a string, got {type(url).__name__}")

    raw_url = url.strip()
    if not raw_url:
        return "unknown"

    # Từ chối nếu chứa khoảng trắng hoặc control characters
    if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in raw_url):
        return "unknown"

    # Chuẩn hóa scheme theo missing scheme rule
    candidate = raw_url
    if candidate.startswith("//"):
        candidate = "https:" + candidate
    elif "://" not in candidate:
        candidate = "https://" + candidate

    try:
        parsed = urlsplit(candidate)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return "unknown"
        # Kiểm tra port: nếu có port thì phải là số nguyên trong khoảng 1-65535
        port = parsed.port
        if port is not None and not (1 <= port <= 65535):
            return "unknown"
        # Xác thực và chuẩn hóa hostname nghiêm ngặt (chống URL rác có khoảng trắng/ký tự lỗi)
        host = normalize_hostname(parsed.hostname)
    except Exception:
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

    # 5. Xử lý AWS S3: Chuẩn hóa cả path-style và virtual-hosted-style về cùng bucket key
    path_segments = [seg for seg in path.strip("/").split("/") if seg]
    if S3_PATH_STYLE_RE.match(host):
        if path_segments and path_segments[0]:
            return f"tenant:s3:{path_segments[0].lower()}"
        return "domain:s3.amazonaws.com"

    if s3_match := S3_VIRTUAL_HOST_RE.match(host):
        bucket = s3_match.group(1).lower()
        return f"tenant:s3:{bucket}"

    # 6. Trích xuất eTLD+1 qua tldextract (đã bao gồm PSL private domains)
    extracted = _EXTRACTOR(host)
    if extracted.ipv4 or extracted.ipv6:
        return f"ip:{extracted.ipv4 or extracted.ipv6}"

    if extracted.domain and extracted.suffix:
        return f"domain:{extracted.domain}.{extracted.suffix}".lower()

    if extracted.domain:
        return f"host:{extracted.domain}".lower()

    return f"host:{host}".lower()
