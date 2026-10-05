"""Script CLI hỗ trợ gán nhãn mù độc lập có bấm giờ tự động (Task LABEL-01).

Dành cho Thành viên A và B thực hiện gán nhãn theo đúng quy chuẩn docs/CODEBOOK_V1.md:
- Bấm giờ chính xác từng mẫu (seconds_spent) tính cả thời gian đọc toàn bộ văn bản.
- Tự động kiểm tra và xác thực enum trước khi ghi vào tệp JSON Lines.
- Hỗ trợ xem toàn bộ văn bản trang hoặc phân trang.
- Kiểm tra an toàn tệp đầu ra (chống nhầm người, nhầm pass_id, chống lẫn bản ghi dry-run).
- Tuyệt đối không âm thầm bỏ qua các dòng JSON lỗi.
- Đọc động codebook_version và random_subset từ dữ liệu/tham số.

Cách sử dụng:
    python scripts/annotate_cli.py --annotator A --input data/annotations/blind_view_pilot.json --output data/annotations/A/pilot_pass1.jsonl
    python scripts/annotate_cli.py --annotator B --input data/annotations/blind_view_pilot.json --output data/annotations/B/pilot_pass1.jsonl
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from typing import Any, Dict, List, Optional, Set

# Đảm bảo mã hóa UTF-8 an toàn trên console Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Thêm src vào sys.path để import phishing
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from phishing.annotation import (
    AnnotationRecord,
    assert_no_label_leak,
    compute_sample_content_hash,
    validate_annotation_record,
)


CLASS_LABEL_CHOICES = {
    "1": "phishing",
    "2": "benign",
    "3": "insufficient_evidence",
}

PRIMARY_ORG_STATUS_CHOICES = {
    "1": "identified",
    "2": "unknown",
    "3": "no_clear_target",
    "4": "multi_target",
}

CATALOG_STATUS_CHOICES = {
    "1": "in_catalog",
    "2": "outside_catalog",
    "3": "unresolved",
}

IDENTITY_ROLE_CHOICES = {
    "1": "identity_claim",
    "2": "mention_only",
    "3": "unclear",
}

DOMAIN_ROLE_CHOICES = {
    "1": "first_party_identity",
    "2": "first_party_content",
    "3": "user_content_hosting",
    "4": "authorized_service",
    "5": "unverified",
}


def prompt_choice(prompt_text: str, choices: Dict[str, str], default_key: str | None = None) -> str:
    """Yêu cầu người dùng chọn từ menu số, hỗ trợ giá trị mặc định."""
    opts_str = " / ".join(f"[{k}] {v}" for k, v in choices.items())
    default_str = f" (Mặc định: [{default_key}])" if default_key else ""
    while True:
        try:
            val = input(f"{prompt_text} ({opts_str}){default_str}: ").strip()
            if not val and default_key:
                return choices[default_key]
            if val in choices:
                return choices[val]
            print(f"Lựa chọn '{val}' không hợp lệ. Vui lòng nhập lại số tương ứng.")
        except EOFError:
            raise KeyboardInterrupt


def load_already_annotated_sample_ids(
    output_path: Path,
    expected_annotator_id: str,
    expected_pass_id: int,
    is_dry_run_session: bool = False,
    expected_dataset_hash: str | None = None,
    expected_dataset_id: str | None = None,
    expected_codebook_hash: str | None = None,
    expected_codebook_version: str | None = None,
    expected_sampling_plan_version: str | None = None,
    current_samples_by_id: Dict[str, Dict[str, Any]] | None = None,
    is_real_session: bool = False,
) -> Set[str]:
    """Đọc các sample_id đã hoàn thành trước đó từ file output JSONL với kiểm tra toàn vẹn nghiêm ngặt."""
    if not output_path.exists():
        return set()

    annotated = set()
    with open(output_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                rec = json.loads(line)
            except json.JSONDecodeError as err:
                raise ValueError(
                    f"LỖI TOÀN VẸN TỆP: Dòng {line_no} trong '{output_path}' không phải JSON hợp lệ ({err}). "
                    f"Không được âm thầm bỏ qua."
                )

            if not isinstance(rec, dict) or not isinstance(rec.get("sample_id"), str) or not rec["sample_id"].strip():
                raise ValueError(f"LỖI TOÀN VẸN TỆP: Dòng {line_no} phải là object có sample_id không rỗng.")

            sid = rec["sample_id"].strip()

            # Từ chối bản ghi có sample_id không thuộc gói hiện tại
            if current_samples_by_id is not None and sid not in current_samples_by_id:
                raise ValueError(
                    f"SAMPLE_ID LẠ: Bản ghi tại dòng {line_no} trong '{output_path}' có sample_id='{sid}' "
                    f"không thuộc gói dữ liệu đầu vào hiện tại. Không được dùng tệp kết quả chứa mẫu lạ!"
                )

            rec_annotator = rec.get("annotator_id")
            rec_pass = rec.get("pass_id")
            rec_is_dry = rec.get("is_dry_run", False)
            rec_dataset_hash = rec.get("dataset_hash")
            rec_dataset_id = rec.get("dataset_id")
            rec_codebook_hash = rec.get("codebook_hash")
            rec_codebook_version = rec.get("codebook_version")
            rec_sampling_plan_version = rec.get("sampling_plan_version")
            rec_sample_hash = rec.get("sample_content_hash")

            # Kiểm tra không dùng nhầm file của người khác
            if rec_annotator != expected_annotator_id:
                raise ValueError(
                    f"MÂU THUẪN ĐÁNH GIÁ VIÊN: Tệp '{output_path}' tại dòng {line_no} chứa kết quả của "
                    f"annotator '{rec_annotator}', trong khi phiên hiện tại đang chạy cho '{expected_annotator_id}'. "
                    f"Bắt buộc tách biệt tệp đầu ra riêng cho từng người gán nhãn!"
                )

            # Kiểm tra không dùng nhầm pass_id
            if rec_pass != expected_pass_id:
                raise ValueError(
                    f"MÂU THUẪN LƯỢT GÁN (PASS_ID): Tệp '{output_path}' tại dòng {line_no} thuộc "
                    f"pass_id={rec_pass}, trong khi phiên hiện tại đang chạy pass_id={expected_pass_id}."
                )

            # Kiểm tra không lẫn bản ghi dry-run vào phiên gán nhãn thật
            if not isinstance(rec_is_dry, bool) or rec_is_dry != is_dry_run_session:
                raise ValueError(
                    f"LỖI TẠP NHIỄM DỮ LIỆU: Tệp '{output_path}' tại dòng {line_no} chứa bản ghi dry-run mô phỏng "
                    f"(is_dry_run=True). Tuyệt đối không được ghi lẫn nhãn mô phỏng vào nhãn thật của người gán."
                )

            # Với phiên thật, yêu cầu đầy đủ các trường provenance
            if is_real_session:
                required_provenance = {
                    "dataset_id": rec_dataset_id,
                    "dataset_hash": rec_dataset_hash,
                    "codebook_version": rec_codebook_version,
                    "codebook_hash": rec_codebook_hash,
                    "sampling_plan_version": rec_sampling_plan_version,
                    "sample_content_hash": rec_sample_hash,
                }
                for p_field, p_val in required_provenance.items():
                    if p_val is None or not str(p_val).strip():
                        raise ValueError(
                            f"THIẾU PROVENANCE: Bản ghi tại dòng {line_no} trong '{output_path}' thiếu trường "
                            f"provenance bắt buộc '{p_field}' cho phiên gán nhãn thực tế."
                        )

            # Khi giá trị kỳ vọng đã xác định, bản ghi thiếu, rỗng hoặc khác giá trị đều phải báo lỗi
            if expected_dataset_hash is not None:
                if rec_dataset_hash is None or str(rec_dataset_hash).strip() != expected_dataset_hash:
                    raise ValueError(
                        f"MÂU THUẪN GÓI DỮ LIỆU ĐẦU VÀO: Tệp '{output_path}' tại dòng {line_no} chứa bản ghi thuộc gói dữ liệu "
                        f"có hash '{rec_dataset_hash}', trong khi phiên hiện tại đang chạy gói có hash '{expected_dataset_hash}'. "
                        f"Tránh dùng nhầm tệp kết quả khi đổi gói dữ liệu!"
                    )
            if expected_dataset_id is not None:
                if rec_dataset_id is None or str(rec_dataset_id).strip() != expected_dataset_id:
                    raise ValueError(
                        f"MÂU THUẪN GÓI DỮ LIỆU ĐẦU VÀO: Tệp '{output_path}' tại dòng {line_no} chứa bản ghi thuộc dataset_id "
                        f"'{rec_dataset_id}', trong khi phiên hiện tại đang chạy dataset_id '{expected_dataset_id}'."
                    )
            if expected_codebook_hash is not None:
                if rec_codebook_hash is None or str(rec_codebook_hash).strip() != expected_codebook_hash:
                    raise ValueError(
                        f"MÂU THUẪN CODEBOOK HASH: Tệp '{output_path}' tại dòng {line_no} chứa bản ghi thuộc codebook_hash "
                        f"'{rec_codebook_hash}', trong khi phiên hiện tại đang chạy codebook_hash '{expected_codebook_hash}'."
                    )
            if expected_codebook_version is not None:
                if rec_codebook_version is None or str(rec_codebook_version).strip() != expected_codebook_version:
                    raise ValueError(
                        f"MÂU THUẪN PHIÊN BẢN CODEBOOK: Tệp '{output_path}' tại dòng {line_no} chứa bản ghi thuộc phiên bản "
                        f"'{rec_codebook_version}', trong khi phiên hiện tại đang chạy '{expected_codebook_version}'."
                    )
            if expected_sampling_plan_version is not None:
                if rec_sampling_plan_version is None or str(rec_sampling_plan_version).strip() != expected_sampling_plan_version:
                    raise ValueError(
                        f"MÂU THUẪN SAMPLING PLAN: Tệp '{output_path}' tại dòng {line_no} chứa bản ghi thuộc sampling_plan_version "
                        f"'{rec_sampling_plan_version}', trong khi phiên hiện tại đang chạy '{expected_sampling_plan_version}'."
                    )

            # Đổi nội dung cùng ID phải bị từ chối; kiểm tra bằng hàm canonical compute_sample_content_hash
            if current_samples_by_id and sid in current_samples_by_id:
                curr_s = current_samples_by_id[sid]
                curr_content_hash = compute_sample_content_hash(curr_s)
                if rec_sample_hash and rec_sample_hash != curr_content_hash:
                    raise ValueError(
                        f"MÂU THUẪN NỘI DUNG MẪU: Mẫu '{sid}' trong '{output_path}' tại dòng {line_no} có hash nội dung "
                        f"'{rec_sample_hash}', khác với nội dung của mẫu cùng ID trong gói đầu vào hiện tại "
                        f"('{curr_content_hash}'). Không được đổi nội dung cùng ID!"
                    )

            if sid in annotated:
                raise ValueError(f"LỖI TOÀN VẸN TỆP: sample_id trùng tại dòng {line_no}.")
            annotated.add(sid)

    return annotated


def display_sample_and_allow_reading(sample: Dict[str, Any], current_idx: int, total_samples: int, interactive: bool = True) -> None:
    """Hiển thị thông tin mẫu và cho phép người gán nhãn đọc toàn bộ văn bản (đồng hồ vẫn tính giờ)."""
    print("\n" + "=" * 80)
    print(f" MẪU GÁN NHÃN MÙ [{current_idx}/{total_samples}]: ID = {sample.get('sample_id')}")
    print("=" * 80)
    print(f"[URL] URL: {sample.get('url')}")

    summary = sample.get("structure_summary", {})
    title = summary.get("title", "")
    if title:
        print(f"[TITLE] Tiêu đề: {title}")

    forms = summary.get("forms", 0)
    inputs = summary.get("inputs", 0)
    pwd = summary.get("password_inputs", 0)
    ext_links = summary.get("external_links", 0)
    has_login = summary.get("has_login_form", False)

    print(f"[DOM] Cấu trúc: Forms: {forms} | Inputs: {inputs} | Passwords: {pwd} (Login Form: {has_login}) | External Links: {ext_links}")
    print("-" * 80)
    print("[TEXT] Nội dung văn bản an toàn:")
    text = sample.get("page_text", "")

    if len(text) > 600:
        print(f"   {text[:600]} ... [Hiển thị trước 600 ký tự]")
        if interactive:
            cursor = 600
            while True:
                try:
                    cmd = input("\n[VĂN BẢN] Nhập 'v' xem toàn bộ (+{} ký tự), 'm' xem thêm 600 ký tự, hoặc Enter để bắt đầu chấm: ".format(len(text) - 600)).strip().lower()
                    if cmd == "v":
                        print("\n--- TOÀN BỘ NỘI DUNG VĂN BẢN ---")
                        print(text)
                        print("-" * 80)
                        break
                    elif cmd == "m":
                        print("\n--- PHẦN VĂN BẢN TIẾP THEO ---")
                        print(text[cursor:cursor + 600] or "[Đã hết văn bản]")
                        cursor += 600
                        print("-" * 80)
                    else:
                        break
                except EOFError:
                    raise KeyboardInterrupt
    else:
        print(f"   {text or '[Không có nội dung văn bản]'}")
    print("-" * 80)


def validate_manifest_preflight(
    manifest_path: Path,
    input_path: Path,
    dataset_data: Dict[str, Any],
    codebook_path: Optional[Path] = None,
    dictionary_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Xác minh toàn diện và đầy đủ trạng thái cũng như mã băm từ manifest trước khi bắt đầu phiên hoặc hiển thị bất kỳ mẫu nào."""
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"LỖI MANIFEST: Không tìm thấy tệp manifest tại '{manifest_path}'."
        )

    try:
        with open(manifest_path, "r", encoding="utf-8") as mf:
            manifest_data = json.load(mf)
    except Exception as e:
        raise ValueError(f"LỖI MANIFEST: Tệp manifest '{manifest_path}' không đúng định dạng JSON: {e}")

    # =========================================================================
    # A. BẮT BUỘC ĐỦ CÁC TRƯỜNG CONTRACT TRONG MANIFEST
    # =========================================================================
    mandatory_fields = [
        "dataset_id",
        "sample_count",
        "sampling_plan_version",
        "codebook_version",
        "codebook_status",
        "dictionary_version",
        "dictionary_status",
        "acceptance",
        "ready_for_annotation",
        "blind_view_sha256",
        "codebook_sha256",
        "dictionary_sha256",
    ]
    for mf_field in mandatory_fields:
        if mf_field not in manifest_data or manifest_data[mf_field] is None:
            raise ValueError(
                f"THIẾU TRƯỜNG MANIFEST BẮT BUỘC: Manifest '{manifest_path}' thiếu trường bắt buộc '{mf_field}'."
            )
        if isinstance(manifest_data[mf_field], str) and not manifest_data[mf_field].strip():
            raise ValueError(
                f"THIẾU TRƯỜNG MANIFEST BẮT BUỘC: Trường '{mf_field}' trong manifest '{manifest_path}' không được để rỗng."
            )

    # =========================================================================
    # B. XÁC MINH TOÀN DIỆN CÁC TRẠNG THÁI (STATUSES) TỪ MANIFEST
    # =========================================================================

    # 1. Trạng thái nghiệm thu hai bên (acceptance B và D)
    acceptance = manifest_data["acceptance"]
    if not isinstance(acceptance, dict):
        raise ValueError(f"LỖI MANIFEST: Trường 'acceptance' trong manifest phải là một đối tượng dict.")
    if acceptance.get("B") != "approved" or acceptance.get("D") != "approved":
        raise ValueError(
            f"CHƯA NGHIỆM THU: Manifest '{manifest_path}' chưa được nghiệm thu đầy đủ bởi cả B và D "
            f"(B: '{acceptance.get('B')}', D: '{acceptance.get('D')}'). Chưa được phép mở phiên gán nhãn!"
        )

    # 2. Cờ sẵn sàng gán nhãn (ready_for_annotation)
    if manifest_data["ready_for_annotation"] is not True:
        raise ValueError(
            f"CHƯA SẴN SÀNG: Manifest '{manifest_path}' có ready_for_annotation={manifest_data.get('ready_for_annotation')}. "
            f"Đợt gán nhãn chưa được mở chính thức!"
        )

    # 3. Trạng thái Codebook (codebook_status)
    cb_status = manifest_data["codebook_status"]
    if cb_status != "locked":
        raise ValueError(
            f"CODEBOOK CHƯA KHÓA: Manifest '{manifest_path}' có codebook_status='{cb_status}' (yêu cầu 'locked')."
        )

    # 4. Phiên bản Codebook (codebook_version) không được ở trạng thái pending
    manifest_cb_ver = str(manifest_data["codebook_version"]).strip()
    if "pending" in manifest_cb_ver.lower():
        raise ValueError(
            f"CODEBOOK CHƯA KHÓA: Manifest '{manifest_path}' khai báo codebook_version='{manifest_cb_ver}' đang ở trạng thái pending."
        )

    # 5. Trạng thái Từ điển (dictionary_status)
    dict_status = manifest_data["dictionary_status"]
    if dict_status != "locked":
        raise ValueError(
            f"DICTIONARY CHƯA KHÓA: Manifest '{manifest_path}' có dictionary_status='{dict_status}' (yêu cầu 'locked')."
        )

    # 6. Phiên bản Từ điển (dictionary_version) không được ở trạng thái pending
    manifest_dict_ver = str(manifest_data["dictionary_version"]).strip()
    if "pending" in manifest_dict_ver.lower():
        raise ValueError(
            f"DICTIONARY CHƯA KHÓA: Manifest '{manifest_path}' khai báo dictionary_version='{manifest_dict_ver}' đang ở trạng thái pending."
        )

    # 7. Số lượng mẫu (sample_count) phải là số nguyên dương, không nhận boolean
    manifest_total = manifest_data["sample_count"]
    if isinstance(manifest_total, bool) or not isinstance(manifest_total, int) or manifest_total <= 0:
        raise ValueError(
            f"LỖI MANIFEST: sample_count trong manifest phải là số nguyên dương, không nhận boolean hoặc <= 0 (nhận: {manifest_total!r})."
        )

    # Riêng REAL-PILOT-32-V1 yêu cầu manifest sample_count đúng 32 mẫu theo kế hoạch đã chốt
    manifest_dataset_id = str(manifest_data["dataset_id"]).strip()
    if manifest_dataset_id == "REAL-PILOT-32-V1" and manifest_total != 32:
        raise ValueError(
            f"LỖI SỐ LƯỢNG MẪU PILOT THẬT: Gói REAL-PILOT-32-V1 yêu cầu manifest sample_count đúng 32 mẫu theo kế hoạch đã chốt (nhận: {manifest_total})."
        )

    # =========================================================================
    # C. XÁC MINH TOÀN DIỆN CÁC MÃ BĂM (HASHES) VÀ ĐỐI CHIẾU ĐĨA THỰC TẾ
    # =========================================================================

    # 1. Mã băm gói Blind View đầu vào (blind_view_sha256)
    manifest_view_hash = str(manifest_data["blind_view_sha256"]).strip()
    if not input_path.exists():
        raise FileNotFoundError(f"THIẾU GÓI BLIND VIEW: Không tìm thấy tệp view tại '{input_path}'.")
    actual_view_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
    if actual_view_hash != manifest_view_hash:
        raise ValueError(
            f"SAI KHÁC MÃ BĂM VIEW: Gói view '{input_path}' có hash '{actual_view_hash}', "
            f"không khớp với manifest ('{manifest_view_hash}')."
        )

    # 2. Mã băm tệp Codebook docs/CODEBOOK_V1.md (codebook_sha256) và kiểm tra nội dung thực tế
    manifest_cb_hash = str(manifest_data["codebook_sha256"]).strip()
    actual_cb_path = codebook_path or (PROJECT_ROOT / "docs" / "CODEBOOK_V1.md")
    if not actual_cb_path.exists():
        raise FileNotFoundError(
            f"THIẾU ARTIFACT CODEBOOK: Không tìm thấy tệp codebook tại '{actual_cb_path}' trên đĩa."
        )
    cb_bytes = actual_cb_path.read_bytes()
    actual_cb_hash = hashlib.sha256(cb_bytes).hexdigest()
    if actual_cb_hash != manifest_cb_hash:
        raise ValueError(
            f"SAI KHÁC MÃ BĂM CODEBOOK: {actual_cb_path} có hash '{actual_cb_hash}', "
            f"không khớp manifest ('{manifest_cb_hash}')."
        )
    if len(cb_bytes.strip()) < 100:
        raise ValueError(f"LỖI NỘI DUNG CODEBOOK: Tệp codebook tại '{actual_cb_path}' rỗng hoặc không đủ nội dung quy chuẩn.")

    # Đọc trạng thái và phiên bản thực tế từ metadata codebook trên đĩa
    cb_text = cb_bytes.decode("utf-8", errors="replace")
    cb_ver_match = re.search(r"\*\*Phiên bản:\*\*\s*(.+)", cb_text)
    cb_status_match = re.search(r"\*\*Trạng thái:\*\*\s*(.+)", cb_text)
    actual_cb_ver = cb_ver_match.group(1).strip().strip("`* ") if cb_ver_match else ""
    actual_cb_status = cb_status_match.group(1).split("(")[0].strip().strip("`* ") if cb_status_match else ""

    if not actual_cb_status or actual_cb_status != "locked" or "pending" in actual_cb_status.lower() or "pending" in actual_cb_ver.lower():
        raise ValueError(
            f"ARTIFACT CODEBOOK CHƯA KHÓA: Tệp codebook tại '{actual_cb_path}' có trạng thái thực tế là '{actual_cb_status}' "
            f"(phiên bản '{actual_cb_ver}'). Bắt buộc codebook trên đĩa phải ở trạng thái 'locked' và không pending."
        )
    if actual_cb_status != cb_status:
        raise ValueError(
            f"SAI KHÁC TRẠNG THÁI CODEBOOK ĐĨA: Tệp codebook trên đĩa có trạng thái '{actual_cb_status}', "
            f"không khớp với trạng thái khai báo trong manifest ('{cb_status}')."
        )
    if actual_cb_ver.lstrip("v") != manifest_cb_ver.lstrip("v"):
        raise ValueError(
            f"SAI KHÁC PHIÊN BẢN CODEBOOK ĐĨA: Tệp codebook trên đĩa có phiên bản '{actual_cb_ver}', "
            f"không khớp với phiên bản khai báo trong manifest ('{manifest_cb_ver}')."
        )

    # 3. Mã băm tệp Từ điển configs/dictionary_v1.json (dictionary_sha256) và kiểm tra nội dung thực tế
    manifest_dict_hash = str(manifest_data["dictionary_sha256"]).strip()
    actual_dict_path = dictionary_path or (PROJECT_ROOT / "configs" / "dictionary_v1.json")
    if not actual_dict_path.exists():
        raise FileNotFoundError(
            f"THIẾU ARTIFACT DICTIONARY: Không tìm thấy tệp từ điển tại '{actual_dict_path}' trên đĩa."
        )
    dict_bytes = actual_dict_path.read_bytes()
    actual_dict_hash = hashlib.sha256(dict_bytes).hexdigest()
    if actual_dict_hash != manifest_dict_hash:
        raise ValueError(
            f"SAI KHÁC MÃ BĂM DICTIONARY: {actual_dict_path} có hash '{actual_dict_hash}', "
            f"không khớp manifest ('{manifest_dict_hash}')."
        )
    try:
        dict_json = json.loads(dict_bytes.decode("utf-8"))
        orgs = dict_json.get("organizations", [])
        if not isinstance(orgs, list) or len(orgs) < 14:
            raise ValueError(f"Từ điển phải chứa ít nhất 14 tổ chức (hiện có: {len(orgs) if isinstance(orgs, list) else 0}).")
    except Exception as e:
        raise ValueError(f"LỖI NỘI DUNG DICTIONARY: Tệp từ điển tại '{actual_dict_path}' không hợp lệ: {e}")

    # Đọc trạng thái và phiên bản thực tế từ dictionary trên đĩa
    actual_dict_status = str(dict_json.get("status", "")).strip()
    actual_dict_version = str(dict_json.get("version", "")).strip()
    if not actual_dict_status or actual_dict_status != "locked" or "pending" in actual_dict_status.lower() or "pending" in actual_dict_version.lower():
        raise ValueError(
            f"ARTIFACT DICTIONARY CHƯA KHÓA: Tệp từ điển tại '{actual_dict_path}' có trạng thái thực tế là '{actual_dict_status}' "
            f"(phiên bản '{actual_dict_version}'). Bắt buộc từ điển trên đĩa phải ở trạng thái 'locked' và không pending."
        )
    if actual_dict_status != dict_status:
        raise ValueError(
            f"SAI KHÁC TRẠNG THÁI DICTIONARY ĐĨA: Tệp từ điển trên đĩa có trạng thái '{actual_dict_status}', "
            f"không khớp với trạng thái khai báo trong manifest ('{dict_status}')."
        )
    if actual_dict_version.lstrip("v") != manifest_dict_ver.lstrip("v"):
        raise ValueError(
            f"SAI KHÁC PHIÊN BẢN DICTIONARY ĐĨA: Tệp từ điển trên đĩa có phiên bản '{actual_dict_version}', "
            f"không khớp với phiên bản khai báo trong manifest ('{manifest_dict_ver}')."
        )

    # =========================================================================
    # D. ĐỐI CHIẾU CHÉO METADATA GIỮA GÓI BLIND VIEW VÀ MANIFEST
    # =========================================================================

    # 1. Dataset ID
    manifest_dataset_id = str(manifest_data["dataset_id"]).strip()
    dataset_id = str(dataset_data.get("dataset_id", "UNKNOWN")).strip()
    if dataset_id != manifest_dataset_id:
        raise ValueError(
            f"SAI KHÁC DATASET_ID: Gói view có dataset_id='{dataset_id}', "
            f"không khớp manifest ('{manifest_dataset_id}')."
        )

    # 2. Số lượng mẫu (sample_count)
    samples = dataset_data.get("samples", [])
    if not isinstance(samples, list) or len(samples) <= 0:
        raise ValueError("LỖI GÓI VIEW: Trường 'samples' phải là một danh sách các mẫu không rỗng.")
    total_samples = len(samples)
    if total_samples != manifest_total:
        raise ValueError(
            f"SAI KHÁC SỐ MẪU: Gói view có {total_samples} mẫu, "
            f"nhưng manifest khai báo {manifest_total} mẫu."
        )
    view_total_samples = dataset_data.get("total_samples")
    if view_total_samples is not None:
        if isinstance(view_total_samples, bool) or not isinstance(view_total_samples, int) or view_total_samples <= 0:
            raise ValueError(
                f"LỖI GÓI VIEW: total_samples trong gói view phải là số nguyên dương, không nhận boolean hoặc <= 0 (nhận: {view_total_samples!r})."
            )
        if int(view_total_samples) != manifest_total:
            raise ValueError(
                f"SAI KHÁC SỐ MẪU: Gói view có total_samples={view_total_samples}, "
                f"không khớp manifest ({manifest_total})."
            )

    # Riêng REAL-PILOT-32-V1 yêu cầu gói view đúng 32 mẫu theo kế hoạch đã chốt
    if (manifest_dataset_id == "REAL-PILOT-32-V1" or dataset_id == "REAL-PILOT-32-V1") and total_samples != 32:
        raise ValueError(
            f"LỖI SỐ LƯỢNG MẪU PILOT THẬT: Gói REAL-PILOT-32-V1 yêu cầu gói view có đúng 32 mẫu theo kế hoạch đã chốt (nhận: {total_samples})."
        )

    # 3. Sampling plan version
    manifest_sp = str(manifest_data["sampling_plan_version"]).strip()
    sampling_plan_version = str(dataset_data.get("sampling_plan_version", "") or "").strip()
    if sampling_plan_version != manifest_sp:
        raise ValueError(
            f"SAI KHÁC SAMPLING_PLAN: Gói view có sampling_plan_version='{sampling_plan_version}', "
            f"không khớp manifest ('{manifest_sp}')."
        )

    # 4. Đối chiếu mã băm codebook và dictionary trong metadata gói view (nếu có khai báo)
    view_cb_hash = dataset_data.get("codebook_sha256") or dataset_data.get("codebook_hash")
    if view_cb_hash and str(view_cb_hash).strip() != manifest_cb_hash:
        raise ValueError(
            f"SAI KHÁC MÃ BĂM CODEBOOK TRONG GÓI: Metadata gói view khai báo codebook hash='{view_cb_hash}', "
            f"không khớp manifest ('{manifest_cb_hash}')."
        )

    view_dict_hash = dataset_data.get("dictionary_sha256")
    if view_dict_hash and str(view_dict_hash).strip() != manifest_dict_hash:
        raise ValueError(
            f"SAI KHÁC MÃ BĂM DICTIONARY TRONG GÓI: Metadata gói view khai báo dictionary hash='{view_dict_hash}', "
            f"không khớp manifest ('{manifest_dict_hash}')."
        )

    view_cb_ver = dataset_data.get("codebook_version")
    if view_cb_ver and str(view_cb_ver).strip().lstrip("v") != manifest_cb_ver.lstrip("v"):
        raise ValueError(
            f"SAI KHÁC PHIÊN BẢN CODEBOOK TRONG GÓI: Metadata gói view khai báo codebook_version='{view_cb_ver}', "
            f"không khớp manifest ('{manifest_cb_ver}')."
        )

    view_dict_ver = dataset_data.get("dictionary_version")
    if view_dict_ver and str(view_dict_ver).strip().lstrip("v") != manifest_dict_ver.lstrip("v"):
        raise ValueError(
            f"SAI KHÁC PHIÊN BẢN DICTIONARY TRONG GÓI: Metadata gói view khai báo dictionary_version='{view_dict_ver}', "
            f"không khớp manifest ('{manifest_dict_ver}')."
        )

    # 5. Đối chiếu phiên bản codebook trên từng mẫu
    for sample in samples:
        if isinstance(sample, dict):
            s_cb_ver = sample.get("codebook_version")
            if s_cb_ver is not None and str(s_cb_ver).strip().lstrip("v") != manifest_cb_ver.lstrip("v"):
                raise ValueError(
                    f"SAI KHÁC PHIÊN BẢN CODEBOOK TRÊN MẪU: Mẫu '{sample.get('sample_id')}' khai báo "
                    f"codebook_version='{s_cb_ver}', không khớp với phiên bản đã kiểm chứng từ manifest ('{manifest_cb_ver}')."
                )

    # =========================================================================
    # E. KIỂM TRA TÍNH DUY NHẤT VÀ HỢP LỆ CỦA SAMPLE_ID TRONG GÓI VIEW
    # =========================================================================
    seen_sids: Set[str] = set()
    for idx, sample in enumerate(samples):
        if not isinstance(sample, dict):
            raise ValueError(f"LỖI TOÀN VẸN MẪU: Mẫu tại vị trí index {idx} không phải là dict.")
        sid = sample.get("sample_id")
        if sid is None or not str(sid).strip():
            raise ValueError(f"LỖI TOÀN VẸN MẪU: Mẫu tại vị trí index {idx} thiếu hoặc rỗng trường 'sample_id'.")
        sid_str = str(sid).strip()
        if sid_str in seen_sids:
            raise ValueError(
                f"LỖI TOÀN VẸN MẪU: Phát hiện sample_id trùng lặp trong danh sách mẫu gói view: '{sid_str}'."
            )
        seen_sids.add(sid_str)

    return manifest_data


def annotate_interactive_session(
    annotator_id: str,
    input_path: Path,
    output_path: Path,
    manifest_path: Path | None = None,
    pass_id: int = 1,
    dry_run: bool = False,
    cli_codebook_version: str | None = None,
    cli_random_subset: bool | None = None,
    codebook_path: Path | None = None,
    dictionary_path: Path | None = None,
) -> None:
    """Phiên làm việc gán nhãn có bấm giờ tương tác."""
    if not input_path.exists():
        raise FileNotFoundError(f"LỖI: Không tìm thấy gói dữ liệu mù tại: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Đảm bảo gói dữ liệu đầu vào không rò rỉ nhãn
    assert_no_label_leak(data)
    samples = data.get("samples", [])
    total_samples = len(samples)

    # Trích xuất thông tin xuất xứ (provenance) của gói dữ liệu
    input_bytes = input_path.read_bytes()
    dataset_hash = hashlib.sha256(input_bytes).hexdigest()
    dataset_id = str(data.get("dataset_id", "UNKNOWN"))
    dataset_type = str(data.get("dataset_type", "blind_view"))
    is_synthetic = bool(data.get("is_synthetic", False))
    sampling_plan_version = str(data.get("sampling_plan_version", "") or "")

    is_real_session = (not dry_run) and (not is_synthetic)
    is_real_pilot = (dataset_id == "REAL-PILOT-32-V1") or (dataset_type in {"real_pilot_ready", "real_pilot_pending_review"})

    # Khóa cờ ghi đè qua CLI trong phiên gán nhãn người thật / phiên thực tế / gói pilot thật
    if (not dry_run) or is_real_session or is_real_pilot:
        if cli_codebook_version is not None:
            raise ValueError(
                "CỜ BỊ KHÓA: Không được ghi đè --codebook-version qua CLI trong phiên gán nhãn người thật / phiên thực tế. "
                "Phiên bản codebook phải lấy từ manifest/gói đã khóa."
            )
        if cli_random_subset is not None:
            raise ValueError(
                "CỜ BỊ KHÓA: Không được ghi đè --random-subset qua CLI trong phiên gán nhãn người thật / phiên thực tế. "
                "Giá trị random_subset phải lấy từ metadata/manifest đã khóa."
            )

    # RÀO CHẮN MANIFEST TOÀN DIỆN: Bắt buộc kiểm tra manifest trước khi hiển thị bất kỳ mẫu nào
    requires_manifest = (
        manifest_path is not None
        or dataset_id == "REAL-PILOT-32-V1"
        or dataset_type in {"real_pilot_ready", "real_pilot_pending_review"}
        or sampling_plan_version == "PILOT-PLAN-V1-FULL-OVERLAP"
        or is_real_session
    )

    manifest_data = None
    if requires_manifest:
        actual_manifest_path = manifest_path or (PROJECT_ROOT / "configs" / "pilot_manifest.json")
        manifest_data = validate_manifest_preflight(
            actual_manifest_path,
            input_path,
            data,
            codebook_path=codebook_path,
            dictionary_path=dictionary_path,
        )

    codebook_hash = str(data.get("codebook_sha256") or data.get("codebook_hash") or "")
    if not codebook_hash:
        cb_path = codebook_path or (PROJECT_ROOT / "docs" / "CODEBOOK_V1.md")
        if cb_path.exists():
            codebook_hash = hashlib.sha256(cb_path.read_bytes()).hexdigest()

    # Xác định phiên bản codebook đã được kiểm chứng
    if manifest_data:
        verified_cb_version = str(manifest_data.get("codebook_version", "")).strip()
    else:
        verified_cb_version = str(data.get("codebook_version") or cli_codebook_version or "").strip()

    # Nếu chạy dry-run và output không được chỉ định tên riêng, dùng file dry-run để cách ly
    actual_output_path = output_path
    if not dry_run and output_path.name.endswith(".dryrun.jsonl"):
        raise ValueError("Không ghi lượt người vào tệp .dryrun.jsonl.")
    if dry_run and not output_path.name.endswith(".dryrun.jsonl"):
        actual_output_path = output_path.with_name(f"{output_path.stem}.dryrun.jsonl")

    actual_output_path.parent.mkdir(parents=True, exist_ok=True)
    samples_by_id = {s.get("sample_id"): s for s in samples if isinstance(s, dict) and s.get("sample_id")}
    done_ids = load_already_annotated_sample_ids(
        actual_output_path,
        expected_annotator_id=f"simulated_{annotator_id}" if dry_run else annotator_id,
        expected_pass_id=pass_id,
        is_dry_run_session=dry_run,
        expected_dataset_hash=dataset_hash,
        expected_dataset_id=dataset_id if dataset_id != "UNKNOWN" else None,
        expected_codebook_hash=codebook_hash or None,
        expected_codebook_version=verified_cb_version or None,
        expected_sampling_plan_version=sampling_plan_version or None,
        current_samples_by_id=samples_by_id,
        is_real_session=is_real_session,
    )

    remaining_samples = [s for s in samples if s.get("sample_id") not in done_ids]
    print(f"\n[START] Khởi động phiên gán nhãn cho Thành viên: {annotator_id}")
    print(f"[PACKAGE] Dataset ID: {dataset_id} | Type: {data.get('dataset_type', 'blind_view')}")
    if is_synthetic:
        print(f"[CHÚ Ý] Đây là gói dữ liệu MÔ PHỎNG ({data.get('purpose', '')})")
    print(f"[SAMPLES] Tổng số mẫu: {total_samples} | Đã hoàn thành: {len(done_ids)} | Còn lại: {len(remaining_samples)}")
    print(f"[OUTPUT] Tệp kết quả: {actual_output_path}")

    if not remaining_samples:
        print("[COMPLETE] Bạn đã hoàn thành toàn bộ các mẫu trong gói này!")
        return

    for idx, sample in enumerate(remaining_samples, len(done_ids) + 1):
        sid = sample.get("sample_id", "UNKNOWN")

        # BẮT BUỘC KIỂM TRA PHIÊN BẢN TRÊN MẪU TRƯỚC KHI HIỂN THỊ
        if verified_cb_version:
            s_cb_ver = sample.get("codebook_version")
            if s_cb_ver is not None and str(s_cb_ver).strip().lstrip("v") != verified_cb_version.lstrip("v"):
                raise ValueError(
                    f"SAI KHÁC PHIÊN BẢN CODEBOOK TRÊN MẪU: Mẫu '{sid}' khai báo "
                    f"codebook_version='{s_cb_ver}', không khớp với phiên bản đã kiểm chứng '{verified_cb_version}'."
                )

        # BẮT ĐẦU ĐỒNG HỒ BẤM GIỜ NGAY TRƯỚC KHI HIỂN THỊ ĐỂ TÍNH CẢ THỜI GIAN ĐỌC
        start_time = time.perf_counter()

        # Hiển thị mẫu và cho phép đọc toàn văn
        display_sample_and_allow_reading(sample, idx, total_samples, interactive=not dry_run)

        # Tính hash nội dung của mẫu hiện tại bằng hàm canonical compute_sample_content_hash
        sample_content_hash = compute_sample_content_hash(sample)

        # Phiên bản codebook luôn lấy theo phiên bản đã kiểm chứng từ manifest/gói đã duyệt
        if verified_cb_version:
            codebook_version = verified_cb_version
        else:
            codebook_version = (
                cli_codebook_version
                or sample.get("codebook_version")
                or data.get("codebook_version")
            )
        if not isinstance(codebook_version, str) or not codebook_version.strip():
            raise ValueError("Thiếu codebook_version trong metadata hoặc tham số CLI.")
        if cli_random_subset is not None:
            if not dry_run:
                raise ValueError("CỜ BỊ KHÓA: Không được ghi đè --random-subset qua CLI trong phiên gán nhãn người thật. Giá trị random_subset phải lấy từ metadata/manifest đã khóa.")
            random_subset = cli_random_subset
        elif "random_subset" in sample:
            random_subset = sample["random_subset"]
        elif "random_subset_default" in data:
            random_subset = data["random_subset_default"]
        else:
            raise ValueError("Thiếu random_subset trong metadata hoặc tham số CLI.")
        if not isinstance(random_subset, bool):
            raise ValueError("random_subset phải là boolean, không phải chuỗi hoặc số.")

        if dry_run:
            # Chế độ dry-run tự động giả lập 1 mẫu để kiểm thử không treo input
            elapsed = 0.5
            record_dict = {
                "annotator_id": f"simulated_{annotator_id}",
                "sample_id": sid,
                "pass_id": pass_id,
                "class_label": "phishing" if "login" in sample.get("url", "") else "benign",
                "primary_org_status": "identified" if "login" in sample.get("url", "") else "unknown",
                "catalog_status": "in_catalog" if "login" in sample.get("url", "") else "unresolved",
                "observed_service": "Office 365" if "office" in sample.get("url", "") else "None",
                "org_targets": ["microsoft"] if "office" in sample.get("url", "") else [],
                "primary_org": "microsoft" if "office" in sample.get("url", "") else "unknown",
                "identity_role": "identity_claim" if "login" in sample.get("url", "") else "unclear",
                "domain_role": "unverified",
                "evidence_note": "Dry-run automated testing record",
                "seconds_spent": elapsed,
                "random_subset": random_subset,
                "difficult_case": False,
                "codebook_version": codebook_version,
                "is_dry_run": True,
                "is_synthetic": is_synthetic,
                "dataset_id": dataset_id,
                "dataset_hash": dataset_hash,
                "codebook_hash": codebook_hash,
                "sampling_plan_version": sampling_plan_version,
                "sample_content_hash": sample_content_hash,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }
            validated_record = validate_annotation_record(record_dict)
            with open(actual_output_path, "a", encoding="utf-8", newline="\n") as out_f:
                out_f.write(json.dumps(validated_record.to_dict(), ensure_ascii=False) + "\n")
            print(f"[OK] [Dry-Run] Đã lưu mẫu {sid} thành công (is_dry_run=True).")
            continue

        try:
            print("\n[INPUT] Nhập thông tin đánh giá (Theo Codebook v1):")
            c_label = prompt_choice("1. Nhãn phân loại", CLASS_LABEL_CHOICES)
            p_org_status = prompt_choice("2. Trạng thái tổ chức", PRIMARY_ORG_STATUS_CHOICES)
            cat_status = prompt_choice("3. Tình trạng từ điển", CATALOG_STATUS_CHOICES)

            obs_service = input("4. Tên dịch vụ quan sát tự do (Enter để bỏ trống): ").strip() or "None"
            primary_org = input("5. Mã tổ chức chính (ví dụ: microsoft, google, unknown): ").strip() or "unknown"

            targets_input = input("6. Các tổ chức bị mạo danh (phân tách bởi dấu phẩy, Enter nếu rỗng): ").strip()
            org_targets = [t.strip() for t in targets_input.split(",") if t.strip()] if targets_input else []
            if primary_org not in {"unknown", "no_clear_target"} and primary_org not in org_targets:
                org_targets.append(primary_org)

            id_role = prompt_choice("7. Vai trò danh tính trên trang", IDENTITY_ROLE_CHOICES)
            dom_role = prompt_choice("8. Vai trò tên miền", DOMAIN_ROLE_CHOICES)

            evidence = input("9. Ghi chú bằng chứng nội dung/form: ").strip() or "Quan sát theo URL và cấu trúc trang"

            diff_str = input("10. Đánh dấu ca khó? [y/N]: ").strip().lower()
            is_diff = diff_str in {"y", "yes", "true", "1"}

            # DỪNG BẤM GIỜ
            elapsed = round(time.perf_counter() - start_time, 2)
            print(f"[TIMER] Thời gian thao tác mẫu (gồm cả thời gian đọc): {elapsed} giây")

            record_dict = {
                "annotator_id": annotator_id,
                "sample_id": sid,
                "pass_id": pass_id,
                "class_label": c_label,
                "primary_org_status": p_org_status,
                "catalog_status": cat_status,
                "observed_service": obs_service,
                "org_targets": org_targets,
                "primary_org": primary_org,
                "identity_role": id_role,
                "domain_role": dom_role,
                "evidence_note": evidence,
                "seconds_spent": elapsed,
                "random_subset": random_subset,
                "difficult_case": is_diff,
                "codebook_version": codebook_version,
                "is_dry_run": False,
                "is_synthetic": is_synthetic,
                "dataset_id": dataset_id,
                "dataset_hash": dataset_hash,
                "codebook_hash": codebook_hash,
                "sampling_plan_version": sampling_plan_version,
                "sample_content_hash": sample_content_hash,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }

            validated_record = validate_annotation_record(record_dict)

            # Ghi nối tiếp ngay vào tệp JSON Lines
            with open(actual_output_path, "a", encoding="utf-8", newline="\n") as out_f:
                out_f.write(json.dumps(validated_record.to_dict(), ensure_ascii=False) + "\n")

            print(f"[OK] Đã lưu kết quả mẫu {sid} vào {actual_output_path}")

        except KeyboardInterrupt:
            print("\n\n[PAUSE] Bạn đã tạm dừng phiên gán nhãn. Tiến độ đã được lưu tự động.")
            print(f"Lần tới bạn có thể chạy lại lệnh để tiếp tục từ mẫu index {idx}.")
            break


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotator", required=True, choices=["A", "B", "adjudicator"], help="Mã người gán nhãn (A, B hoặc adjudicator)")
    parser.add_argument("--input", default="data/annotations/blind_view_pilot.json", type=Path, help="Đường dẫn tệp Blind View đầu vào")
    parser.add_argument("--output", required=True, type=Path, help="Đường dẫn tệp JSONL xuất kết quả gán nhãn")
    parser.add_argument("--pass-id", default=1, type=int, help="Lượt gán nhãn: 1 (độc lập), 2 (phân xử)")
    parser.add_argument("--dry-run", action="store_true", help="Chạy tự động không chờ nhập liệu bàn phím (dùng cho CI/test)")
    parser.add_argument("--codebook-version", default=None, help="Phiên bản Codebook áp dụng (mặc định lấy từ metadata tệp mẫu)")
    parser.add_argument("--random-subset", default=None, type=lambda x: (str(x).lower() in ['true','1', 'yes']), help="Chỉ định mẫu thuộc random subset")
    parser.add_argument("--manifest", default=None, type=Path, help="Đường dẫn tệp Manifest kiểm định")

    args = parser.parse_args()
    annotate_interactive_session(
        annotator_id=args.annotator,
        input_path=args.input,
        output_path=args.output,
        manifest_path=args.manifest,
        pass_id=args.pass_id,
        dry_run=args.dry_run,
        cli_codebook_version=args.codebook_version,
        cli_random_subset=args.random_subset,
    )


if __name__ == "__main__":
    main()
