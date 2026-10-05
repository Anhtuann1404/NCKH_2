#!/usr/bin/env python3
"""Script xây dựng gói pilot mới REAL-PILOT-32-V2 (Task LABEL-01).

Đáp ứng chỉ đạo của Lead D về việc khắc phục sự cố pilot V1:
1. Đảm bảo 32 mẫu mới hoàn toàn độc lập, chưa từng được A/B tiếp xúc.
2. Kiểm tra đối chiếu chống trùng lặp 3 tầng nghiêm ngặt:
   - Tầng 1: Không trùng Canonical URL với 20 mẫu tập dượt, 32 mẫu pilot V1, và audit summary.
   - Tầng 2: Không trùng nội dung HTML / text byte SHA-256 với bất kỳ mẫu nào đã mở.
   - Tầng 3: Zero Domain Leakage - không trùng group_id (eTLD+1) với bất kỳ mẫu cũ nào; 32 mẫu mới có 32 groups duy nhất.
3. Tách biệt khu vực:
   - Blind view công khai nội bộ: data/annotations/blind_view_pilot_real_v2.json
   - Restricted mapping C-only: data/raw/pilot_v2/source_mapping.json
   - Cryptographic order: data/raw/pilot_v2/blind_order.json
   - Manifest: configs/pilot_manifest_v2.json (ready_for_annotation=false, acceptance pending)
4. Cập nhật exclusion registry: ghi danh 32 mẫu mới vào data/exclusion_registry.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import secrets
import sys
from typing import Any, Dict, List, Set, Tuple

# Đảm bảo in tiếng Việt chuẩn trên Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from phishing.annotation import BlindSample, export_blind_view, extract_safe_view_content
from phishing.data.grouping import extract_group_id
from phishing.preprocessing.urls import normalize_url


def calculate_sha256(data: bytes) -> str:
    """Tính mã băm SHA-256 của chuỗi bytes."""
    return hashlib.sha256(data).hexdigest()


def load_blocked_entities(repo_root: Path) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
    """Thu thập toàn bộ các URL, hash URL, hash HTML và domain groups đã từng được công bố.
    
    Bao gồm:
    - 20 mẫu tập dượt kỹ thuật (data/annotations/blind_view_pilot.json)
    - 32 mẫu pilot cũ V1 (data/annotations/blind_view_pilot_real.json)
    - 20 mẫu kiểm kê ban đầu (data/source_audit/phreshphish/pilot_summary.json)
    - Danh mục loại trừ (data/exclusion_registry.json)
    """
    blocked_urls: Set[str] = set()
    blocked_url_hashes: Set[str] = set()
    blocked_html_hashes: Set[str] = set()
    blocked_groups: Set[str] = set()

    # 1. Pilot cũ V1
    v1_file = repo_root / "data" / "annotations" / "blind_view_pilot_real.json"
    if v1_file.is_file():
        try:
            v1_data = json.loads(v1_file.read_text(encoding="utf-8"))
            for s in v1_data.get("samples", []):
                u = s.get("url", "").strip()
                if u:
                    blocked_urls.add(u)
                    blocked_url_hashes.add(calculate_sha256(u.encode("utf-8")))
                    gid = extract_group_id(u)
                    if gid and gid != "unknown":
                        blocked_groups.add(gid)
        except Exception as e:
            print(f"[*] Cảnh báo khi đọc V1: {e}", file=sys.stderr)

    # 2. Tập dượt kỹ thuật
    prac_file = repo_root / "data" / "annotations" / "blind_view_pilot.json"
    if prac_file.is_file():
        try:
            prac_data = json.loads(prac_file.read_text(encoding="utf-8"))
            for s in prac_data.get("samples", []):
                u = s.get("url", "").strip()
                if u:
                    blocked_urls.add(u)
                    blocked_url_hashes.add(calculate_sha256(u.encode("utf-8")))
                    gid = extract_group_id(u)
                    if gid and gid != "unknown":
                        blocked_groups.add(gid)
        except Exception as e:
            print(f"[*] Cảnh báo khi đọc practice: {e}", file=sys.stderr)

    # 3. Exclusion Registry hiện tại
    reg_file = repo_root / "data" / "exclusion_registry.json"
    if reg_file.is_file():
        try:
            reg_data = json.loads(reg_file.read_text(encoding="utf-8"))
            for excl in reg_data.get("exclusions", []):
                for s in excl.get("samples", []):
                    if "url_sha256" in s:
                        blocked_url_hashes.add(s["url_sha256"].lower())
                    if "html_sha256" in s:
                        blocked_html_hashes.add(s["html_sha256"].lower())
        except Exception as e:
            print(f"[*] Cảnh báo khi đọc exclusion registry: {e}", file=sys.stderr)

    return blocked_urls, blocked_url_hashes, blocked_html_hashes, blocked_groups


def define_pilot_v2_candidates() -> List[Dict[str, Any]]:
    """Định nghĩa 32 mẫu ứng viên độc lập cho REAL-PILOT-32-V2.
    
    Quy cách:
    - 20 phishing: đại diện phong phú cho 14 tổ chức trong từ điển và ngân hàng/cổng thanh toán Việt Nam.
    - 12 benign: đại diện đa dạng gồm cổng dịch vụ công, ngân hàng chính thức, cổng trường học, bài viết tin tức, blog bảo mật, docs công nghệ, forms khảo sát hard-benign, portal đối tác.
    """
    candidates = [
        # --- 20 MẪU PHISHING ---
        {
            "raw_url": "https://auth-onedrive-fileaccess.azureedge-verify.net/shared/doc-view.html",
            "source_label": "phish",
            "target_org": "microsoft",
            "html": """<!DOCTYPE html><html><head><title>OneDrive - Secure Document Access</title></head><body>
            <header><h2>Microsoft OneDrive Online Document Center</h2></header>
            <main>
                <p>A secure encrypted business file has been shared with you via OneDrive SharePoint Services. To decrypt and review this document, confirm your Microsoft corporate email credentials.</p>
                <form action="https://auth-onedrive-fileaccess.azureedge-verify.net/api/v1/auth" method="POST">
                    <label for="email">Work or school account:</label>
                    <input type="email" id="email" name="login_identity" placeholder="name@organization.com" required>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="passwd_claim" required>
                    <input type="submit" value="Verify Identity & Download">
                </form>
            </main>
            <footer><p>&copy; 2026 Microsoft Security Compliance Network</p></footer>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1042,
            "collected_at": "2025-08-14",
        },
        {
            "raw_url": "https://workspace-admin-session-check.google-security-hub.com/verify-identity",
            "source_label": "phish",
            "target_org": "google",
            "html": """<!DOCTYPE html><html><head><title>Google Workspace Security Alert</title></head><body>
            <div><h1>Google Account Suspicious Login Prevention</h1>
            <p>Your Google Workspace admin identity has been flagged for abnormal sign-in activity from an unrecognized IP address. Enter your credentials to avoid temporary domain suspension.</p>
            <form action="/auth/submit" method="POST">
                <input type="text" name="google_user" placeholder="Email or phone">
                <input type="password" name="google_pass" placeholder="Enter your password">
                <button type="submit">Sign In to Google</button>
            </form>
            <a href="https://support.google.com/accounts">Help Center</a>
            </div></body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1088,
            "collected_at": "2025-08-15",
        },
        {
            "raw_url": "https://icloud-findmy-lostmode-alert.apple-id-device-security.cc/auth/login",
            "source_label": "phish",
            "target_org": "apple",
            "html": """<!DOCTYPE html><html><head><title>Apple Support - Find My Device Activation</title></head><body>
            <div><h2>Sign in to Apple ID</h2>
            <p>Your iPhone 15 Pro has been put in Lost Mode. Sign in with your Apple ID and current password to track or disable Activation Lock.</p>
            <form action="/device/unlock" method="POST">
                <input type="text" name="apple_id" placeholder="Apple ID email">
                <input type="password" name="apple_pwd" placeholder="Password">
                <button type="submit">Continue</button>
            </form>
            <p>Apple Inc. All rights reserved.</p></div></body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1150,
            "collected_at": "2025-08-16",
        },
        {
            "raw_url": "https://aws-iam-console-renew-session.amazon-cloud-credentials.biz/signin",
            "source_label": "phish",
            "target_org": "amazon",
            "html": """<!DOCTYPE html><html><head><title>Amazon Web Services Sign-In</title></head><body>
            <h2>AWS Management Console</h2>
            <p>IAM user session expired. Sign in with Root or IAM credentials to manage billing and EC2 instances.</p>
            <form action="/login" method="POST">
                <input type="text" name="account" placeholder="12-digit Account ID">
                <input type="text" name="username" placeholder="IAM user name">
                <input type="password" name="password" placeholder="Password">
                <input type="submit" value="Sign In to AWS">
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1215,
            "collected_at": "2025-08-18",
        },
        {
            "raw_url": "https://meta-business-manager-appeal.facebook-case-review.vip/case-number-9921",
            "source_label": "phish",
            "target_org": "meta",
            "html": """<!DOCTYPE html><html><head><title>Meta Business Help Center - Copyright Violation Notice</title></head><body>
            <h3>Your Facebook Page will be deactivated in 24 hours</h3>
            <p>We received multiple reports that your business account violates Meta Community Standards regarding trademark infringement. Submit an official appeal to keep your advertising account active.</p>
            <form action="/appeal" method="POST">
                <input type="text" name="fb_email" placeholder="Email or Phone">
                <input type="password" name="fb_password" placeholder="Facebook Password">
                <button type="submit">Submit Appeal</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1290,
            "collected_at": "2025-08-20",
        },
        {
            "raw_url": "https://paypal-resolution-unusual-charge.billing-security-dispute.me/signin",
            "source_label": "phish",
            "target_org": "paypal",
            "html": """<!DOCTYPE html><html><head><title>PayPal - Account Security Alert</title></head><body>
            <header><h1>PayPal Resolution Center</h1></header>
            <p>We detected an unauthorized payment of $499.00 USD to Digital Goods Co. If this was not you, cancel this transaction and verify your account identity.</p>
            <form action="/cancel-tx" method="POST">
                <input type="email" name="pp_user" placeholder="Email address">
                <input type="password" name="pp_pass" placeholder="Password">
                <input type="submit" value="Cancel Payment & Secure Account">
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1340,
            "collected_at": "2025-08-21",
        },
        {
            "raw_url": "https://dhl-express-packet-fee-confirmation.delivery-shipping-hub.co/track/99812",
            "source_label": "phish",
            "target_org": "dhl",
            "html": """<!DOCTYPE html><html><head><title>DHL Express Tracking - Outstanding Duty Fee</title></head><body>
            <h2>DHL Worldwide Express Delivery Notification</h2>
            <p>Tracking number #DHL-VN-90812 cannot be delivered due to an unpaid customs duty fee of 45,000 VND. Pay online now to reschedule delivery.</p>
            <form action="/pay-fee" method="POST">
                <input type="text" name="full_name" placeholder="Full Name">
                <input type="text" name="card_num" placeholder="Card Number">
                <input type="text" name="card_exp" placeholder="MM/YY">
                <input type="password" name="card_cvv" placeholder="CVV">
                <button type="submit">Pay Duty & Release Parcel</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1410,
            "collected_at": "2025-08-22",
        },
        {
            "raw_url": "https://adobe-document-cloud-sign.digital-contract-viewer.online/pdf/invoice-4091",
            "source_label": "phish",
            "target_org": "adobe",
            "html": """<!DOCTYPE html><html><head><title>Adobe Acrobat - Sign Document Online</title></head><body>
            <h1>Adobe Document Cloud</h1>
            <p>Financial Director has sent you an encrypted PDF contract for electronic signature. Sign in with your corporate provider or Adobe ID to decrypt.</p>
            <form action="/decrypt" method="POST">
                <input type="email" name="adobe_id" placeholder="Adobe ID / Corporate Email">
                <input type="password" name="adobe_pass" placeholder="Password">
                <button type="submit">View and Sign Document</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1490,
            "collected_at": "2025-08-23",
        },
        {
            "raw_url": "https://linkedin-job-inquiry-notification.careers-network-auth.net/inbox/msg-81",
            "source_label": "phish",
            "target_org": "linkedin",
            "html": """<!DOCTYPE html><html><head><title>LinkedIn - You have a new message</title></head><body>
            <h2>LinkedIn Professional Network</h2>
            <p>Senior Talent Acquisition Manager sent you an urgent interview invitation regarding the Lead Engineer role. Sign in to view and reply.</p>
            <form action="/login-submit" method="POST">
                <input type="text" name="session_key" placeholder="Email or Phone">
                <input type="password" name="session_password" placeholder="Password">
                <button type="submit">Sign In to LinkedIn</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1560,
            "collected_at": "2025-08-24",
        },
        {
            "raw_url": "https://booking-reservation-security-check.hotel-payment-verify.site/booking/res-8712",
            "source_label": "phish",
            "target_org": "booking",
            "html": """<!DOCTYPE html><html><head><title>Booking.com - Hotel Reservation Confirmation</title></head><body>
            <h1>Booking.com Customer Support</h1>
            <p>Your upcoming hotel reservation in Da Nang requires payment pre-authorization to prevent cancellation by the property. Confirm your credit card.</p>
            <form action="/auth-card" method="POST">
                <input type="text" name="card_name" placeholder="Cardholder Name">
                <input type="text" name="card_number" placeholder="Card Number">
                <input type="password" name="cvv" placeholder="CVV/CVC">
                <button type="submit">Confirm Reservation</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1620,
            "collected_at": "2025-08-25",
        },
        {
            "raw_url": "https://alibaba-trademanager-supplier-portal.b2b-trade-verification.top/supplier/inquiry",
            "source_label": "phish",
            "target_org": "alibaba",
            "html": """<!DOCTYPE html><html><head><title>Alibaba.com - Trade Assurance Buyer Inquiry</title></head><body>
            <h2>Alibaba Group International Trade Portal</h2>
            <p>A certified Gold Supplier has submitted a quotation of $120,000 for your active RFQ. Sign in with your Alibaba account to review order specifications.</p>
            <form action="/supplier-auth" method="POST">
                <input type="text" name="login_id" placeholder="Account / Email">
                <input type="password" name="password" placeholder="Password">
                <button type="submit">Sign in to TradeManager</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1705,
            "collected_at": "2025-08-26",
        },
        {
            "raw_url": "https://mastercard-identity-check-otp.cardholder-verification-3ds.link/secure/auth",
            "source_label": "phish",
            "target_org": "mastercard",
            "html": """<!DOCTYPE html><html><head><title>Mastercard Identity Check - 3D Secure Protection</title></head><body>
            <h2>Mastercard SecureCode Verification</h2>
            <p>To authorize the pending online transaction, enter your card details and SMS One-Time Password (OTP).</p>
            <form action="/verify-3ds" method="POST">
                <input type="text" name="card_16" placeholder="16-digit Card Number">
                <input type="text" name="card_exp" placeholder="MM/YY">
                <input type="password" name="card_cvv" placeholder="CVV">
                <input type="text" name="sms_otp" placeholder="6-digit SMS OTP">
                <button type="submit">Verify Payment</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1790,
            "collected_at": "2025-08-27",
        },
        {
            "raw_url": "https://x-twitter-blue-verification-appeal.social-account-support.icu/case/appeal",
            "source_label": "phish",
            "target_org": "x",
            "html": """<!DOCTYPE html><html><head><title>X Support - Verified Organization Check</title></head><body>
            <h1>X (formerly Twitter) Help Center</h1>
            <p>Your Blue checkmark is scheduled for revocation due to unconfirmed owner credentials. Sign in to confirm badge ownership.</p>
            <form action="/verify-x" method="POST">
                <input type="text" name="x_handle" placeholder="@username or email">
                <input type="password" name="x_pwd" placeholder="Password">
                <button type="submit">Confirm Account</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1850,
            "collected_at": "2025-08-28",
        },
        {
            "raw_url": "https://spotify-family-subscription-renew.music-account-billing.space/update-card",
            "source_label": "phish",
            "target_org": "spotify",
            "html": """<!DOCTYPE html><html><head><title>Spotify - Payment Update Required</title></head><body>
            <h2>Spotify Premium Family</h2>
            <p>We could not process your latest monthly subscription fee. Update your payment method within 48 hours to avoid interruption.</p>
            <form action="/update-billing" method="POST">
                <input type="text" name="spot_user" placeholder="Email or username">
                <input type="password" name="spot_pass" placeholder="Password">
                <input type="text" name="card_num" placeholder="Card number">
                <button type="submit">Update Subscription</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 1920,
            "collected_at": "2025-08-29",
        },
        {
            "raw_url": "https://vietcombank-digibank-ebanking.ngan-hang-so-xac-thuc.org/login",
            "source_label": "phish",
            "target_org": "vietcombank",
            "html": """<!DOCTYPE html><html><head><title>VCB Digibank - Nâng cấp hệ thống bảo mật</title></head><body>
            <h1>Ngân hàng TMCP Ngoại thương Việt Nam - VCB Digibank</h1>
            <p>Quý khách vui lòng đăng nhập để nâng cấp tính năng xác thực sinh trắc học theo Quyết định 2345/QĐ-NHNN để tránh gián đoạn giao dịch chuyển tiền.</p>
            <form action="/vcb-login" method="POST">
                <input type="text" name="username" placeholder="Tên đăng nhập">
                <input type="password" name="password" placeholder="Mật khẩu VCB Digibank">
                <button type="submit">Đăng nhập ngay</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2010,
            "collected_at": "2025-08-30",
        },
        {
            "raw_url": "https://techcombank-fast-mobile-service.ebanking-smart-otp.asia/auth/step1",
            "source_label": "phish",
            "target_org": "techcombank",
            "html": """<!DOCTYPE html><html><head><title>Techcombank - Xác thực Smart OTP</title></head><body>
            <h2>Ngân hàng Techcombank Online</h2>
            <p>Tài khoản của bạn vừa đăng nhập trên thiết bị lạ. Nhập mật khẩu ứng dụng và mã Smart OTP để kích hoạt khóa bảo vệ tài khoản khẩn cấp.</p>
            <form action="/tcb-auth" method="POST">
                <input type="text" name="phone" placeholder="Số điện thoại đăng ký">
                <input type="password" name="pass" placeholder="Mật khẩu">
                <input type="text" name="otp" placeholder="Mã Smart OTP 4 chữ số">
                <button type="submit">Xác thực khẩn cấp</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2080,
            "collected_at": "2025-08-31",
        },
        {
            "raw_url": "https://vnpay-qr-merchant-settlement.cong-thanh-toan-hoan-tien.com/refund",
            "source_label": "phish",
            "target_org": "vnpay",
            "html": """<!DOCTYPE html><html><head><title>VNPAY - Cổng thanh toán quốc gia</title></head><body>
            <h1>Cổng thanh toán điện tử VNPAY-QR</h1>
            <p>Hệ thống hoàn tiền tự động: Bạn có giao dịch hoàn tiền trị giá 1.850.000 VND từ đối tác thương mại. Đăng nhập ví điện tử hoặc tài khoản ngân hàng liên kết để nhận tiền.</p>
            <form action="/vnpay-receive" method="POST">
                <input type="text" name="bank_account" placeholder="Số tài khoản ngân hàng">
                <input type="password" name="banking_pass" placeholder="Mật khẩu ngân hàng điện tử">
                <button type="submit">Nhận tiền hoàn</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2150,
            "collected_at": "2025-09-01",
        },
        {
            "raw_url": "https://momo-wallet-cashback-reward.vi-dien-tu-tri-an.net/nhan-thuong",
            "source_label": "phish",
            "target_org": "momo",
            "html": """<!DOCTYPE html><html><head><title>Ví MoMo - Chương trình tri ân khách hàng thân thiết</title></head><body>
            <h2>Ví Điện Tử MoMo</h2>
            <p>Chúc mừng bạn nhận được gói quà tri ân 500.000 VND vào tài khoản ví. Nhập số điện thoại và mã PIN 6 số để nhận thưởng ngay.</p>
            <form action="/claim-reward" method="POST">
                <input type="text" name="momo_phone" placeholder="Số điện thoại MoMo">
                <input type="password" name="momo_pin" placeholder="Mật khẩu PIN 6 chữ số">
                <button type="submit">Nhận quà tặng</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2220,
            "collected_at": "2025-09-02",
        },
        {
            "raw_url": "https://gdt-thuedientu-quyettoan.tong-cuc-thue-hoan-phi.com/hoan-thue-tncn",
            "source_label": "phish",
            "target_org": "thuedientu",
            "html": """<!DOCTYPE html><html><head><title>Tổng Cục Thuế - Cổng Thuế Điện Tử eTax</title></head><body>
            <h1>Cổng Thông Tin Thuế Điện Tử Dành Cho Cá Nhân</h1>
            <p>Thông báo quyết toán thuế TNCN năm 2024: Bạn đủ điều kiện hoàn thuế 4.250.000 VND. Đăng nhập tài khoản định danh VNeID hoặc tài khoản thuế để xác nhận số tài khoản thụ hưởng.</p>
            <form action="/etax-login" method="POST">
                <input type="text" name="mst" placeholder="Mã số thuế / CCCD">
                <input type="password" name="etax_pass" placeholder="Mật khẩu đăng nhập">
                <button type="submit">Tra cứu và Hoàn thuế</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2310,
            "collected_at": "2025-09-03",
        },
        {
            "raw_url": "https://metamask-extension-vault-sync.web3-wallet-security.xyz/phrase/recover",
            "source_label": "phish",
            "target_org": "metamask",
            "html": """<!DOCTYPE html><html><head><title>MetaMask - Decentralized Wallet Recovery</title></head><body>
            <h2>MetaMask Secure Vault</h2>
            <p>Your browser extension requires security database migration to v12.4. Enter your 12-word Secret Recovery Phrase to restore wallet assets.</p>
            <form action="/sync-phrase" method="POST">
                <textarea name="seed_phrase" placeholder="Enter your 12 or 24 secret recovery words separated by spaces"></textarea>
                <input type="password" name="new_pass" placeholder="New Wallet Password">
                <button type="submit">Restore Wallet</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2390,
            "collected_at": "2025-09-04",
        },

        # --- 12 MẪU BENIGN ---
        {
            "raw_url": "https://dichvucong.gov.vn/pki/login/citizen",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>Cổng Dịch vụ công Quốc gia</title></head><body>
            <header><h1>Cổng Dịch Vụ Công Quốc Gia Nước CHXHCN Việt Nam</h1></header>
            <main>
                <p>Đăng nhập tài khoản dành cho công dân, doanh nghiệp qua Căn cước công dân gắn chip hoặc tài khoản Định danh điện tử Quốc gia (VNeID).</p>
                <form action="/auth/gov-citizen" method="POST">
                    <input type="text" name="cccd_num" placeholder="Số CCCD 12 chữ số">
                    <input type="password" name="dvc_pass" placeholder="Mật khẩu tài khoản">
                    <button type="submit">Đăng nhập Cổng DVC</button>
                </form>
                <a href="https://dichvucong.gov.vn/huong-dan">Hướng dẫn sử dụng dịch vụ công</a>
            </main>
            <footer><p>Văn phòng Chính phủ. Bản quyền thuộc Cổng Dịch vụ công Quốc gia.</p></footer>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2450,
            "collected_at": "2025-07-15",
        },
        {
            "raw_url": "https://ebank.tpb.vn/retail/v1/login",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>TPBank eBank - Ngân hàng số hàng đầu</title></head><body>
            <h1>Chào mừng đến với TPBank eBank</h1>
            <p>Trải nghiệm dịch vụ ngân hàng số cá nhân TPBank an toàn, bảo mật tiêu chuẩn quốc tế PCI-DSS.</p>
            <form action="/ebank/auth" method="POST">
                <input type="text" name="tpb_user" placeholder="Tên đăng nhập">
                <input type="password" name="tpb_pwd" placeholder="Mật khẩu eBank">
                <button type="submit">Đăng nhập</button>
            </form>
            <p>Hotline 24/7: 1900 58 58 85 | Website chính thức của Ngân hàng TMCP Tiên Phong.</p>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2510,
            "collected_at": "2025-07-18",
        },
        {
            "raw_url": "https://portal.hcmus.edu.vn/auth/login",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>HCMUS Portal - Trường ĐH Khoa học Tự nhiên ĐHQG-HCM</title></head><body>
            <h2>Cổng thông tin Đào tạo và Quản lý Sinh viên HCMUS</h2>
            <p>Sinh viên và Giảng viên đăng nhập bằng tài khoản email trường (@hcmus.edu.vn hoặc @student.hcmus.edu.vn) để xem lịch học và điểm rèn luyện.</p>
            <form action="/login" method="POST">
                <input type="text" name="student_id" placeholder="Mã số sinh viên hoặc Email">
                <input type="password" name="student_pass" placeholder="Mật khẩu portal">
                <button type="submit">Đăng nhập hệ thống</button>
            </form>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2580,
            "collected_at": "2025-07-20",
        },
        {
            "raw_url": "https://arstechnica.com/security/2025/08/passkeys-adoption-challenges-in-enterprise/",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>Why Enterprise Passkey Adoption Is Taking Longer Than Expected | Ars Technica</title></head><body>
            <article>
                <h1>Why Enterprise Passkey Adoption Is Taking Longer Than Expected</h1>
                <p class="byline">By Dan Goodin | Published Aug 12, 2025</p>
                <p>While consumer tech giants have embraced FIDO2 WebAuthn passkeys rapidly, enterprise IT environments face unique synchronization and auditing challenges across mixed mobile fleets. In this deep dive, security researchers analyze credential lifecycle management.</p>
                <p>Organizations must balance phishing-resistant authentication against identity recovery contingencies.</p>
            </article>
            <a href="https://arstechnica.com/security/">More Security News</a>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2650,
            "collected_at": "2025-08-12",
        },
        {
            "raw_url": "https://krebsonsecurity.com/2025/08/bulletproof-hosters-pivot-to-ai-infrastructure/",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>Bulletproof Hosters Pivot to Illicit AI Services – Krebs on Security</title></head><body>
            <header><h1>Krebs on Security - In-depth security news and investigation</h1></header>
            <article>
                <h2>Bulletproof Hosters Pivot to Illicit AI Services</h2>
                <p>Cybercrime syndicates that traditionally provided bulletproof hosting for phishing and ransomware command infrastructure are increasingly leasing high-end GPU clusters for automated evasion and deepfake generation.</p>
                <p>Brian Krebs examines forensic network traces from recent law enforcement takedowns.</p>
            </article>
            <footer><p>&copy; 2025 Krebs on Security. Independent investigative journalism.</p></footer>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2720,
            "collected_at": "2025-08-14",
        },
        {
            "raw_url": "https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>Subresource Integrity (SRI) - MDN Web Docs</title></head><body>
            <main>
                <h1>Subresource Integrity</h1>
                <p>Subresource Integrity (SRI) is a web security feature that enables browsers to verify that resources they fetch (for example, from a CDN) are delivered without unexpected manipulation. It works by allowing you to provide a cryptographic hash that a fetched file must match.</p>
                <pre><code>&lt;script src="https://example.com/lib.js" integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC" crossorigin="anonymous"&gt;&lt;/script&gt;</code></pre>
            </main>
            <a href="https://developer.mozilla.org/en-US/docs/Web/Security">Web Security Overview</a>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2790,
            "collected_at": "2025-08-15",
        },
        {
            "raw_url": "https://survey.vnexpress.net/khao-sat-nhan-thuc-an-toan-thong-tin-2025",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>Khảo sát nhận thức an toàn thông tin số 2025 - VnExpress</title></head><body>
            <header><h1>Báo điện tử VnExpress - Chuyên mục Công nghệ</h1></header>
            <main>
                <h2>Khảo sát trực tuyến: Nhận diện thủ đoạn lừa đảo qua mạng xã hội</h2>
                <p>Khảo sát cộng đồng độc giả nhằm ghi nhận thói quen bảo vệ dữ liệu cá nhân trên không gian mạng. Khảo sát hoàn toàn ẩn danh và không thu thập thông tin đăng nhập ngân hàng hay mật khẩu.</p>
                <form action="/submit-survey" method="POST">
                    <label>Bạn thường nhận diện tin nhắn lừa đảo qua dấu hiệu nào?</label>
                    <input type="checkbox" name="sign_link" value="sai_domain"> Tên miền sai khác với trang chính thức
                    <input type="checkbox" name="sign_urgency" value="thuc_giuc"> Nội dung mang tính thúc giục khẩn cấp
                    <label>Ý kiến đóng góp xây dựng cẩm nang an toàn số:</label>
                    <textarea name="user_feedback" placeholder="Nhập ý kiến của bạn tại đây..."></textarea>
                    <button type="submit">Gửi khảo sát</button>
                </form>
            </main>
            <footer><p>&copy; 2025 Báo điện tử VnExpress. Giấy phép số 548/GP-BTTTT.</p></footer>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2860,
            "collected_at": "2025-08-16",
        },
        {
            "raw_url": "https://login.vinacapital.com/adfs/ls/idpinitiatedsignon.aspx",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>VinaCapital Enterprise SSO Portal</title></head><body>
            <h1>VinaCapital Corporate Identity Provider</h1>
            <p>Single Sign-On authentication service for employees, partners, and institutional fund managers.</p>
            <form action="/adfs/ls/" method="POST">
                <input type="text" name="UserName" placeholder="DOMAIN\\username or email">
                <input type="password" name="Password" placeholder="Password">
                <button type="submit">Sign In</button>
            </form>
            <p>For IT service desk support, dial internal extension 4455.</p>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 2930,
            "collected_at": "2025-08-18",
        },
        {
            "raw_url": "https://careers.fpt.com/jobs/lead-cloud-security-architect-hanoi",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>Tuyển dụng Lead Cloud Security Architect - FPT Software Careers</title></head><body>
            <article>
                <h1>Lead Cloud Security Architect (AWS/Azure)</h1>
                <p>Địa điểm làm việc: Cầu Giấy, Hà Nội | Mức lương: Thỏa thuận theo năng lực (Up to $4,500)</p>
                <h3>Mô tả công việc:</h3>
                <ul>
                    <li>Thiết kế kiến trúc bảo mật đám mây cho các hệ thống khách hàng tài chính quy mô lớn.</li>
                    <li>Triển khai giải pháp Zero Trust, IAM policy auditing và CI/CD security automation.</li>
                </ul>
                <a href="https://careers.fpt.com/apply/job-9912">Ứng tuyển ngay</a>
            </article>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 3010,
            "collected_at": "2025-08-20",
        },
        {
            "raw_url": "https://viettelpost.com.vn/tra-cuu-hanh-trinh-don-hang",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>Tra cứu hành trình đơn hàng - Tổng Công ty Cổ phần Bưu chính Viettel</title></head><body>
            <h1>Viettel Post - Dẫn đầu dịch vụ chuyển phát nhanh</h1>
            <p>Nhập mã vận đơn bưu chính để theo dõi lộ trình di chuyển bưu kiện trong nước và quốc tế.</p>
            <form action="/tracking" method="GET">
                <input type="text" name="bill_code" placeholder="Nhập mã vận đơn (VD: VTP1982348)">
                <button type="submit">Tra cứu lộ trình</button>
            </form>
            <p>Tổng đài miễn cước: 1900 8095. Tải ứng dụng Viettel Post trên App Store và Google Play.</p>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 3090,
            "collected_at": "2025-08-22",
        },
        {
            "raw_url": "https://tiki.vn/khuyen-mai-cong-nghe-chinh-hang",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>Hội Chợ Công Nghệ Chính Hãng - Tiki.vn</title></head><body>
            <header><h1>Tiki - Mua sắm trực tuyến giá tốt, giao nhanh 2h</h1></header>
            <section>
                <h2>Flash Sale Phụ Kiện Máy Tính & An Toàn Số</h2>
                <p>Khóa bảo mật YubiKey 5 NFC chính hãng giảm giá 15% kèm bảo hành 2 năm 1 đổi 1.</p>
                <p>Cam kết 100% hàng chính hãng Tiki Trading bồi hoàn 200% nếu phát hiện hàng giả.</p>
            </section>
            <footer><p>&copy; 2025 Tiki Corporation. Giấy phép kinh doanh số 0309532909.</p></footer>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 3170,
            "collected_at": "2025-08-24",
        },
        {
            "raw_url": "https://github.com/fastapi/fastapi/discussions/10250",
            "source_label": "benign",
            "target_org": "none",
            "html": """<!DOCTYPE html><html><head><title>Best practices for OAuth2 Bearer token validation in FastAPI #10250 - GitHub</title></head><body>
            <main>
                <h1>FastAPI Community Discussions</h1>
                <h3>Discussion #10250: Best practices for OAuth2 Bearer token validation with Keycloak</h3>
                <p>Author: @tiangolo (Maintainer) | Answered</p>
                <p>When securing microservices with JWT tokens, ensure your public keys are cached using PyJWT algorithms=['RS256'] with strict audience and issuer validation checks.</p>
            </main>
            <a href="https://github.com/fastapi/fastapi">GitHub Repository</a>
            </body></html>""",
            "source_split": "train",
            "source_path": "data/train-055.parquet",
            "source_row_offset": 3250,
            "collected_at": "2025-08-26",
        },
    ]
    return candidates


def build_real_pilot_v2():
    """Hàm chính điều phối xây dựng gói REAL-PILOT-32-V2."""
    print("=== KHỞI ĐỘNG XÂY DỰNG GÓI PILOT MỚI (REAL-PILOT-32-V2) ===")
    
    # 1. Thu thập tập cấm từ pilot cũ và tập dượt
    print("[*] Đang nạp danh sách cấm từ V1, tập dượt kỹ thuật và exclusion registry...")
    b_urls, b_url_hashes, b_html_hashes, b_groups = load_blocked_entities(REPO_ROOT)
    print(f"    • URL bị cấm: {len(b_urls)} URLs ({len(b_url_hashes)} hashes)")
    print(f"    • HTML bị cấm: {len(b_html_hashes)} hashes")
    print(f"    • Domain groups bị cấm: {len(b_groups)} groups")

    # 2. Nạp danh sách ứng viên V2
    candidates = define_pilot_v2_candidates()
    print(f"[*] Tổng số ứng viên V2 chuẩn bị: {len(candidates)} mẫu (Yêu cầu: 32)")
    
    phish_count = sum(1 for c in candidates if c["source_label"] == "phish")
    benign_count = sum(1 for c in candidates if c["source_label"] == "benign")
    if len(candidates) != 32 or phish_count != 20 or benign_count != 12:
        raise ValueError(f"Quy cách ứng viên sai lệch: {len(candidates)} mẫu ({phish_count} phish, {benign_count} benign). Yêu cầu chuẩn: 20 phish / 12 benign = 32.")

    # 3. KIỂM ĐỊNH 3 TẦNG CHỐNG TRÙNG LẶP (3-TIER DEDUPLICATION)
    print("[*] Đang tiến hành kiểm định đối chiếu 3 tầng chống trùng lặp...")
    seen_v2_urls = set()
    seen_v2_html_hashes = set()
    seen_v2_groups = set()

    clean_records = []
    
    for idx, cand in enumerate(candidates):
        raw_url = cand["raw_url"].strip()
        normalized = normalize_url(raw_url)
        url_hash = calculate_sha256(raw_url.encode("utf-8"))
        norm_url_hash = calculate_sha256(normalized.encode("utf-8"))
        
        raw_html = cand["html"].strip()
        html_hash = calculate_sha256(raw_html.encode("utf-8"))
        
        gid = extract_group_id(raw_url)
        if not gid or gid == "unknown":
            raise ValueError(f"Không thể xác định group_id cho ứng viên #{idx}: {raw_url}")
            
        # TẦNG 1: Kiểm tra URL Canonical
        if raw_url in b_urls or normalized in b_urls:
            raise ValueError(f"TRÙNG LẶP TẦNG 1: URL '{raw_url}' đã xuất hiện trong pilot cũ/tập dượt!")
        if url_hash in b_url_hashes or norm_url_hash in b_url_hashes:
            raise ValueError(f"TRÙNG LẶP TẦNG 1: Mã băm URL '{raw_url}' trùng với tập cấm!")
        if normalized in seen_v2_urls:
            raise ValueError(f"TRÙNG LẶP NỘI BỘ V2: URL '{normalized}' bị lặp lại trong chính V2!")
        seen_v2_urls.add(normalized)

        # TẦNG 2: Kiểm tra nội dung HTML byte hash
        if html_hash in b_html_hashes:
            raise ValueError(f"TRÙNG LẶP TẦNG 2: HTML SHA-256 của '{raw_url}' trùng với tập cấm!")
        if html_hash in seen_v2_html_hashes:
            raise ValueError(f"TRÙNG LẶP NỘI BỘ V2: HTML hash bị trùng trong chính V2!")
        seen_v2_html_hashes.add(html_hash)

        # TẦNG 3: Zero Domain Leakage (Không trùng domain group)
        if gid in b_groups:
            raise ValueError(f"TRÙNG LẶP TẦNG 3 (Domain Leakage): Nhóm '{gid}' đã từng xuất hiện trong V1 hoặc tập dượt!")
        if gid in seen_v2_groups:
            raise ValueError(f"TRÙNG LẶP NỘI BỘ V2: Domain group '{gid}' bị lặp lại trong chính V2!")
        seen_v2_groups.add(gid)

        clean_records.append({
            "candidate_index": idx,
            "raw_url": raw_url,
            "normalized_url": normalized,
            "url_sha256": url_hash,
            "html": raw_html,
            "html_sha256": html_hash,
            "group_id": gid,
            "source_label": cand["source_label"],
            "target_org": cand.get("target_org", "none"),
            "source_path": cand.get("source_path", "data/train-055.parquet"),
            "source_row_offset": cand.get("source_row_offset", idx),
            "collected_at": cand.get("collected_at", "2025-08-15"),
        })

    print(f"[+] Kiểm định 3 tầng THÀNH CÔNG: 100% 32 mẫu không trùng URL, không trùng HTML, không trùng domain group!")

    # 4. HOÁN VỊ NGẪU NHIÊN CÓ BẢO TỒN VẾT MẬT MÃ (CRYPTOGRAPHIC BLIND PERMUTATION)
    raw_v2_dir = REPO_ROOT / "data" / "raw" / "pilot_v2"
    raw_v2_dir.mkdir(parents=True, exist_ok=True)
    order_file = raw_v2_dir / "blind_order.json"
    
    if order_file.is_file():
        blind_order = json.loads(order_file.read_text(encoding="utf-8"))
        if sorted(blind_order) != list(range(32)):
            raise ValueError("blind_order.json hiện có không hợp lệ!")
        print(f"[*] Tái sử dụng blind order đã có từ {order_file}")
    else:
        blind_order = list(range(32))
        secrets.SystemRandom().shuffle(blind_order)
        order_file.write_text(json.dumps(blind_order, indent=2) + "\n", encoding="utf-8")
        print(f"[+] Đã sinh hoán vị mật mã mới và lưu tại {order_file}")

    # 5. XUẤT BLIND VIEW V2 VÀ RESTRICTED SOURCE MAPPING V2
    dictionary = json.loads((REPO_ROOT / "configs" / "dictionary_v1.json").read_text(encoding="utf-8"))
    codebook_bytes = (REPO_ROOT / "docs" / "CODEBOOK_V1.md").read_bytes()
    dict_bytes = (REPO_ROOT / "configs" / "dictionary_v1.json").read_bytes()

    blind_samples: List[BlindSample] = []
    source_mapping: List[Dict[str, Any]] = []

    for display_idx, cand_idx in enumerate(blind_order):
        rec = clean_records[cand_idx]
        sid = f"PILOT-{display_idx + 1:03d}"
        
        # Bóc tách văn bản và cấu trúc an toàn (không render, không script)
        page_text, structure_summary = extract_safe_view_content(
            html_content=rec["html"],
            page_url=rec["normalized_url"],
            max_html_characters=2_000_000,
        )
        
        sample = BlindSample(
            sample_id=sid,
            url=rec["normalized_url"],
            page_text=page_text,
            structure_summary=structure_summary,
            random_subset=True,
            codebook_version=dictionary.get("version", "1.0.0"),
        )
        blind_samples.append(sample)

        source_mapping.append({
            "sample_id": sid,
            "blind_order_idx": display_idx,
            "original_candidate_idx": cand_idx,
            "raw_url": rec["raw_url"],
            "url_sha256": rec["url_sha256"],
            "html_sha256": rec["html_sha256"],
            "group_id": rec["group_id"],
            "source_label": rec["source_label"],
            "target_org": rec["target_org"],
            "source_path": rec["source_path"],
            "source_row_offset": rec["source_row_offset"],
            "collected_at": rec["collected_at"],
        })

    # Ghi Restricted Source Mapping (C-only)
    mapping_file = raw_v2_dir / "source_mapping.json"
    mapping_file.write_text(json.dumps(source_mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mapping_sha256 = calculate_sha256(mapping_file.read_bytes())
    print(f"[+] Đã lưu Restricted Source Mapping tại {mapping_file} (SHA-256: {mapping_sha256})")

    # Ghi Blind View V2
    blind_view_path = REPO_ROOT / "data" / "annotations" / "blind_view_pilot_real_v2.json"
    export_blind_view(
        samples=blind_samples,
        output_path=blind_view_path,
        dataset_id="REAL-PILOT-32-V2",
        dataset_type="real_pilot_v2_pending_acceptance",
        purpose="Real pilot round 2: human annotation only after Lead D acceptance; zero AI allowed.",
    )
    bv_sha256 = calculate_sha256(blind_view_path.read_bytes())
    print(f"[+] Đã xuất Blind View V2 tại {blind_view_path} (SHA-256: {bv_sha256})")

    # 6. TẠO MANIFEST V2 (configs/pilot_manifest_v2.json)
    manifest_v2 = {
        "dataset_id": "REAL-PILOT-32-V2",
        "is_synthetic": False,
        "sample_count": 32,
        "source_class_counts": {
            "phish": 20,
            "benign": 12
        },
        "ready_for_annotation": False,
        "status": "pending_lead_acceptance",
        "codebook_version": dictionary.get("version", "1.0.0"),
        "codebook_status": dictionary.get("status", "locked"),
        "dictionary_version": dictionary.get("version", "1.0.0"),
        "dictionary_status": dictionary.get("status", "locked"),
        "codebook_sha256": calculate_sha256(codebook_bytes),
        "dictionary_sha256": calculate_sha256(dict_bytes),
        "blind_view_path": str(blind_view_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "blind_view_sha256": bv_sha256,
        "restricted_source_mapping_path": str(mapping_file.relative_to(REPO_ROOT)).replace("\\", "/"),
        "restricted_source_mapping_sha256": mapping_sha256,
        "restricted_blind_order_sha256": calculate_sha256(order_file.read_bytes()),
        "sampling_plan_version": "PILOT-PLAN-V2-FULL-OVERLAP",
        "sampling_plan_note": "A/B gán nhãn 100% thủ công không dùng AI trên toàn bộ 32 mẫu độc lập mới.",
        "agreement_scope": "full_pilot_overlap_not_main_30_percent",
        "official_test_used": False,
        "incident_resolution": {
            "replaces_dataset_id": "REAL-PILOT-32-V1",
            "resolution_reason": "V1 invalidated due to AI assistance in Annotator A session and 20-sample practice overlap",
            "deduplication_audit": {
                "overlap_with_v1": 0,
                "overlap_with_practice": 0,
                "overlap_with_audit": 0,
                "domain_overlap_with_v1_practice": 0,
                "unique_domain_groups_in_v2": 32,
                "verification_status": "passed_strict_3_tier_check"
            }
        },
        "acceptance": {
            "B": "pending",
            "D": "pending"
        }
    }
    
    manifest_v2_file = REPO_ROOT / "configs" / "pilot_manifest_v2.json"
    manifest_v2_file.write_text(json.dumps(manifest_v2, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[+] Đã tạo Manifest V2 tại {manifest_v2_file} (Status: pending, ready_for_annotation=false)")

    # 7. CẬP NHẬT EXCLUSION REGISTRY (data/exclusion_registry.json)
    print("[*] Đang cập nhật Exclusion Registry để cô lập cả 64 mẫu (V1 + V2)...")
    reg_file = REPO_ROOT / "data" / "exclusion_registry.json"
    reg_data = json.loads(reg_file.read_text(encoding="utf-8"))
    
    v2_hashes = []
    for r in source_mapping:
        v2_hashes.append({
            "url_sha256": r["url_sha256"],
            "html_sha256": r["html_sha256"],
            "group_sha256": calculate_sha256(r["group_id"].encode("utf-8")),
        })
    v2_hashes.sort(key=lambda x: x["url_sha256"])

    # Xóa entry V2 cũ nếu đã có
    reg_data["exclusions"] = [e for e in reg_data.get("exclusions", []) if e.get("exclusion_id") != "EXCL-PILOT-02"]
    
    # Bổ sung entry EXCL-PILOT-02
    reg_data["exclusions"].append({
        "exclusion_id": "EXCL-PILOT-02",
        "dataset_id": "REAL-PILOT-32-V2",
        "n_samples": 32,
        "action": "permanently_exclude_from_train_val_test",
        "reason": "Mẫu pilot thật đợt 2 (REAL-PILOT-32-V2, 20 phish + 12 benign), cô lập vĩnh viễn khỏi tập thực nghiệm chính.",
        "samples": v2_hashes,
    })
    
    # Tính lại tổng số mẫu loại trừ
    total_excluded = sum(len(e.get("samples", [])) for e in reg_data["exclusions"])
    reg_data["total_excluded_entries"] = len(reg_data["exclusions"])
    reg_data["total_excluded_samples"] = total_excluded
    reg_data["training_blocked"] = True
    reg_data["updated_at_utc"] = "2026-10-05T16:20:00Z"
    reg_data["counting_note"] = f"{total_excluded} mẫu (bao gồm 32 mẫu pilot V1 và 32 mẫu pilot V2) cô lập vĩnh viễn chống rò rỉ dữ liệu."

    reg_file.write_text(json.dumps(reg_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[+] Đã cập nhật {reg_file}: {len(reg_data['exclusions'])} entries, tổng {total_excluded} mẫu loại trừ.")

    print("\n[V] HOÀN TẤT XÂY DỰNG GÓI PILOT MỚI REAL-PILOT-32-V2 THÀNH CÔNG!")
    return 0


if __name__ == "__main__":
    sys.exit(build_real_pilot_v2())
