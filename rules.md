# 🚀 CẨM NANG WORKFLOW & QUY TẮC LÀM VIỆC CHUẨN NCKH_2 (NCKH)
> *"Code sạch — Sync chuẩn — Test xanh — Docs đủ — Ping nhanh"*

Chào cả team! Để dự án nghiên cứu **NCKH_2** chạy mượt mà, dữ liệu và kết quả thực nghiệm luôn có tính tái lập (reproducible), tránh rò rỉ dữ liệu (data leakage) và giúp bạn Lead (D) review/merge nhanh nhất, tất cả thành viên khi bắt đầu phiên làm việc hoặc nhận task mới vui lòng tuân thủ nghiêm ngặt **Quy trình 6 bước** dưới đây.

---

## 📋 TỔNG QUAN QUY TRÌNH 6 BƯỚC

```mermaid
flowchart TD
    B1["1. Sync develop<br/>(git pull & merge)"] --> B2["2. Nạp ngữ cảnh cho AI<br/>(Đọc CURRENT_TASKS, TECH_SPEC...)"]
    B2 --> B3["3. Code & Self-Check<br/>(compile, test 100% pass)"]
    B3 --> B4["4. Cập nhật Docs & Task<br/>(docs/CURRENT_TASKS.md, spec)"]
    B4 --> B5["5. Push nhánh & Tạo PR<br/>(Target: develop)"]
    B5 --> B6["6. Ping Discord<br/>(Báo PR hoặc Báo Block)"]
```

---

## 🔄 BƯỚC 1: ĐỒNG BỘ CODE MỚI NHẤT TỪ DEVELOP (ALWAYS SYNC FIRST)

Trước khi gõ bất kỳ dòng code nào hay mở phiên làm việc mới, việc đầu tiên là phải lấy code mới nhất về máy:

```bash
# 1. Chuyển sang nhánh develop và kéo code mới nhất về
git checkout develop
git pull origin develop

# 2. Quay lại nhánh làm việc của bạn và gộp code mới từ develop vào
git checkout feature/<tên-nhánh-của-bạn>
git merge develop
```

> [!IMPORTANT]
> **Quy tắc:** Tuyệt đối không code trên một nhánh đã lỗi thời so với `develop` để tránh xung đột đè nát code của nhau.

---

## 🧠 BƯỚC 2: NẠP NGỮ CẢNH CHO AI TRƯỚC KHI CODE (CONTEXT IS KING)

Nếu bạn dùng AI Agent (Antigravity, Cursor, Claude, ChatGPT...), đừng vội yêu cầu AI viết code ngay. Hãy để AI đọc hiểu kiến trúc và ranh giới phân công trước:

1. **Yêu cầu AI đọc các tài liệu liên quan:**
   - Đọc task hiện tại: [docs/CURRENT_TASKS.md](docs/CURRENT_TASKS.md)
   - Đọc quy chuẩn kỹ thuật & giao thức: [docs/TECH_SPEC.md](docs/TECH_SPEC.md), [docs/DATA_PROTOCOL.md](docs/DATA_PROTOCOL.md) (nếu làm dữ liệu), [docs/EXPERIMENT_PROTOCOL.md](docs/EXPERIMENT_PROTOCOL.md) (nếu làm mô hình), [docs/API_SPEC.md](docs/API_SPEC.md) (nếu làm API/Extension).
   - Đọc cẩm nang AI Agent: [AGENTS.md](AGENTS.md).
2. **Khoanh vùng phạm vi theo đúng vai trò (A/B/C/D):** 
   - Nhắc AI rõ ràng: *"Chỉ sửa các file thuộc phân công của mình (ví dụ: Thành viên C chỉ sửa `src/phishing/data/`, `src/phishing/annotation/`, `configs/` phần dữ liệu; tuyệt đối không tự ý sửa code huấn luyện model của D hoặc can thiệp nhãn độc lập của A/B)."*

---

## 🛠️ BƯỚC 3: CODE VÀ TỰ KIỂM CHỨNG (SELF-CHECK 100% PASS)

Code xong chưa phải là xong! Bạn phải tự tay chạy kiểm chứng xem máy mình có chạy được không:

1. **Kiểm tra sạch conflict markers (Không để sót rác Git):**
   ```bash
   git grep -E "^(<<<<<<<|=======|>>>>>>>)"
   ```
   *(Lệnh này không được hiện ra bất kỳ dòng nào)*

2. **Kiểm tra cú pháp Python (Tránh đẩy code bị SyntaxError):**
   ```bash
   python3 -m py_compile src/phishing/<module-vừa-sửa>.py
   # Ví dụ: python3 -m py_compile src/phishing/preprocessing/url_cleaner.py
   ```

3. **Chạy bộ Unit Test với Fixtures an toàn (Phải xanh lá 100%):**
   ```bash
   pytest tests/<file_test_của_bạn>.py
   # Ví dụ: pytest tests/test_url_parser.py
   ```

> [!TIP]
> **Quy tắc:** Chỉ khi tất cả các test đều **PASS**, không có lỗi cú pháp và không vi phạm quy tắc an toàn (không fetch mạng sống, không chạy JS nguy hại) thì mới chuyển sang Bước 4.

---

## 📝 BƯỚC 4: NHỜ AI CẬP NHẬT DOCS & TASK TIẾN ĐỘ (BẮT BUỘC SAU MỖI PHIÊN)

Code đã chạy ngon, trước khi commit, **hãy yêu cầu AI cập nhật lại tài liệu và nhật ký tiến độ** của phiên làm việc đó:

1. **Cập nhật danh sách Task ([docs/CURRENT_TASKS.md](docs/CURRENT_TASKS.md)):**
   - Đổi trạng thái task từ `TODO`/`IN_PROGRESS` sang `DONE` khi đã có artifact kiểm chứng được.
   - Dẫn link file bằng chứng (proof path) vào task tương ứng.
2. **Ghi nhật ký tiến độ:**
   - Thêm dòng mới vào mục *Nhật ký cập nhật* trong [docs/CURRENT_TASKS.md](docs/CURRENT_TASKS.md) hoặc [docs/Ghi_chu_nghien_cuu.md](docs/Ghi_chu_nghien_cuu.md) ghi rõ ngày tháng, tóm tắt việc đã làm và kết quả kiểm thử.
3. **Cập nhật tài liệu kỹ thuật chuyên môn:**
   - Nếu có tạo API mới, sửa regex domain rules hay thay đổi schema manifest, nhờ AI cập nhật ngay vào [docs/TECH_SPEC.md](docs/TECH_SPEC.md), [docs/DATA_PROTOCOL.md](docs/DATA_PROTOCOL.md) hoặc [docs/API_SPEC.md](docs/API_SPEC.md).

> [!IMPORTANT]
> **Quy tắc:** Không để "code đi trước, tài liệu ở lại phía sau". Sau mỗi phiên, tài liệu phải phản ánh đúng 100% hiện trạng code và dữ liệu.

---

## 📤 BƯỚC 5: PUSH LÊN NHÁNH RIÊNG & TẠO PULL REQUEST (PR)

Khi cả Code, Test và Docs đều đã đồng bộ:

1. **Commit và Push lên nhánh của bạn trên GitHub:**
   ```bash
   git add <các_file_code_test_va_docs_da_sua>
   git commit -m "feat(<task-id>): mô tả ngắn gọn việc bạn đã làm + update docs"
   git push origin feature/<tên-nhánh-của-bạn>
   ```

2. **Lên GitHub tạo Pull Request (PR):**
   - Base branch (nhánh đích): `develop`
   - Compare branch (nhánh của bạn): `feature/<tên-nhánh-của-bạn>`
   - Ghi mô tả ngắn: Mã Task ID, các file đã sửa, tình trạng test pass, tài liệu đã cập nhật.
    
> [!WARNING]
> **LƯU Ý QUAN TRỌNG:** **KHÔNG ĐƯỢC TỰ BẤM MERGE!** Hãy để Lead (D) kiểm tra thay đổi (diff), xác nhận không rò rỉ dữ liệu và Lead sẽ là người bấm merge vào `develop`.

---

## 📢 BƯỚC 6: THÔNG BÁO NGAY LÊN DISCORD (KEEP TEAM IN THE LOOP)

Mỗi khi bạn hoàn thành hoặc gặp khó khăn, hãy bắn tin lên kênh Discord của nhóm theo mẫu sau:

* **Trường hợp 1: Khi hoàn thành task & tạo PR xong:**
  > 🎯 `@Lead` Mình vừa tạo PR cho task **[Mã Task - Tên task]**!  
  > 🔗 **Link PR:** `https://github.com/.../pull/...`  
  > 🧪 **Tình trạng:** Đã self-check, pass 100% unit tests, đã cập nhật `docs/CURRENT_TASKS.md`. Nhờ Lead review và merge giúp mình nhé!

* **Trường hợp 2: Khi gặp bug hóc búa, bị block hoặc có thắc mắc kỹ thuật:**
  > 🛑 `@Team` Mình đang làm task **[Mã Task]** thì bị vướng ở đoạn **[mô tả lỗi ngắn gọn]**.  
  > 📌 **Chi tiết/File:** `src/phishing/...` hoặc `data/...`  
  > 💡 Cần mọi người hỗ trợ cùng gỡ đoạn này giúp mình với!

---

## ⛔ 4 ĐIỀU TUYỆT ĐỐI "CẤM KỴ" (RED FLAGS) TRONG NCKH_2

| STT | Điều cấm kỵ | Lý do / Hậu quả đối với đề tài NCKH |
| :---: | :--- | :--- |
| ❌ 1 | **Không push code chưa chạy thử** | Tuyệt đối không đẩy code lỗi cú pháp hoặc test đang fail lên repo chung làm hỏng môi trường của người khác. |
| ❌ 2 | **Không quên cập nhật docs** | Code xong mà không cập nhật `docs/CURRENT_TASKS.md` coi như chưa hoàn thành task; các thành viên khác sẽ mất phương hướng. |
| ❌ 3 | **Không vi phạm ranh giới vai trò & Chống rò rỉ dữ liệu** | Data pipeline (C) không tự ý sửa model/serving của D; D không can thiệp giao diện mù của C; Annotator (A/B) không tự ý sửa codebook; Tuyệt đối không dùng nhãn test để sửa features/threshold. |
| ❌ 4 | **Không "ôm việc âm thầm" khi bị kẹt** | Nếu bị bug/block quá 2 tiếng mà không giải quyết được, **bắt buộc** phải hú lên Discord để cả team cùng hỗ trợ! |

---

🎯 *Chúc cả team NCKH_2 phối hợp mượt mà, code bon bon, nghiên cứu chặt chẽ và cùng nhau đưa đề tài về đích rực rỡ nhé!* 🚀
