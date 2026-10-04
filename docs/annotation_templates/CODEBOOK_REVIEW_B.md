# BÃ¡o cÃ¡o RÃ  soÃ¡t Äá»™c láº­p GÃ³i LABEL-01, Codebook v1.0 & Dictionary v1 (ThÃ nh viÃªn B)

**Dá»± Ã¡n:** NCKH_2 â€” PhÃ¡t hiá»‡n website phishing máº¡o danh tá»• chá»©c
**NgÆ°á»i rÃ  soÃ¡t:** PhÃ¹ng Táº¥n Minh (ThÃ nh viÃªn B â€” QA & Kiá»ƒm nhÃ£n Ä‘á»™c láº­p)
**NhÃ¡nh lÃ m viá»‡c:** `docs/member-b-start01`
**Äá»‘i tÆ°á»£ng rÃ  soÃ¡t:** NhÃ¡nh `origin/feat/data-pipeline` táº¡i cÃ¡c commit:
* `7fe0239`: Xá»­ lÃ½ rÃ  soÃ¡t ban Ä‘áº§u (provenance, allowlist, dry-run, resume)
* `ccdfdbb`: BÃ¡o cÃ¡o há»c thuáº­t cá»§a C gá»­i Lead D (78 tests pass)
* `6817d7e`: Báº£n sá»­a Ä‘á»•i báº£o tá»“n ca khÃ³ ngáº«u nhiÃªn, CLI metadata Ä‘á»™ng vÃ  builder pilot tháº­t (86 tests)
**NgÃ y thá»±c hiá»‡n:** 04/10/2026
**PhÆ°Æ¡ng thá»©c kiá»ƒm tra:** RÃ  soÃ¡t mÃ£ nguá»“n qua Git inspection Ä‘á»™c láº­p, Ä‘á»‘i soÃ¡t vÄƒn liá»‡u nguá»“n Check Point, cháº¡y kiá»ƒm thá»­ tá»± Ä‘á»™ng vÃ  phÃ¢n tÃ­ch ká»‹ch báº£n biÃªn trong mÃ´i trÆ°á»ng thá»­ nghiá»‡m CPython 3.14.2 / pytest 9.1.1.

---

## ðŸ“Œ Káº¾T LUáº¬N Tá»”NG THá»‚

> [!IMPORTANT]
> **Káº¾T LUáº¬N Cá»¦A THÃ€NH VIÃŠN B:**
> 1. NhÃ³m phÃ¡t triá»ƒn (C vÃ  Kháº£i) Ä‘Ã£ cÃ³ nhá»¯ng bÆ°á»›c tiáº¿n ká»¹ thuáº­t quan trá»ng táº¡i commit `7fe0239` vÃ  `6817d7e`, kháº¯c phá»¥c háº§u háº¿t cÃ¡c lá»— há»•ng logic ban Ä‘áº§u cá»§a CLI vÃ  bá»™ lá»c Cohen's Kappa.
> 2. **Tuy nhiÃªn, há»‡ thá»‘ng váº«n CHÆ¯A Äá»¦ ÄIá»€U KIá»†N TIáº¾N HÃ€NH PILOT Báº¤M GIá»œ Äá»‚ CHá»T QUY MÃ” PLAN-01** do 3 Ä‘iá»ƒm then chá»‘t:
>    - **ChÆ°a tÃ¡ch báº¡ch schema dá»¯ liá»‡u mÃ´ phá»ng:** `AnnotationRecord` thiáº¿u cÃ¡c trÆ°á»ng `is_synthetic`, `dataset_id`, `dataset_hash`. NgÆ°á»i gÃ¡n nhÃ£n thá»±c hiá»‡n trÃªn fixture mock váº«n sinh ra báº£n ghi `is_dry_run=False`, cÃ³ nguy cÆ¡ láº«n vÃ o sá»‘ liá»‡u nghiÃªn cá»©u.
>    - **Resume chÆ°a Ä‘á»‘i chiáº¿u gÃ³i dá»¯ liá»‡u:** ChÆ°a kiá»ƒm tra `dataset_id` / `package_hash` vÃ  `codebook_hash`. Äá»•i gÃ³i dá»¯ liá»‡u nhÆ°ng trÃ¹ng `sample_id` váº«n bá»‹ coi lÃ  Ä‘Ã£ hoÃ n thÃ nh.
>    - **Lá»—i mÃ´i trÆ°á»ng phá»¥ thuá»™c:** Suite kiá»ƒm thá»­ `test_label_fixes.py` bá»‹ lá»—i 2 tests do mÃ´i trÆ°á»ng thiáº¿u gÃ³i `tldextract` (chÆ°a cÃ i Ä‘áº·t theo `requirements.txt`).
> 3. **Tráº¡ng thÃ¡i bÃ n giao:** B **chÆ°a thá»±c hiá»‡n gÃ¡n nhÃ£n pilot tháº­t**, **chÆ°a kÃ½ duyá»‡t Ä‘Ã³ng bÄƒng Codebook/Dictionary** (tiáº¿p tá»¥c giá»¯ `pending_review`). Giá»¯ nguyÃªn tráº¡ng thÃ¡i `TODO` cá»§a task LABEL-01, chá» C hoÃ n thiá»‡n cÃ¡c Ä‘iá»ƒm cÃ²n thiáº¿u vÃ  Lead D chÃ­nh thá»©c phÃ¡t lá»‡nh má»Ÿ pilot.

---

## 1. Báº¢NG Äá»’NG Bá»˜ THEO DÃ•I CÃC MÃƒ Lá»–I (R-B01â€“R-B04 VÃ€ L-B01â€“L-B06)

Báº£ng tá»•ng há»£p tÃ¬nh tráº¡ng xá»­ lÃ½ cÃ¡c khuyáº¿n nghá»‹ vÃ  lá»—i ká»¹ thuáº­t Ä‘Ã£ phÃ¡t hiá»‡n:

| MÃ£ lá»—i | YÃªu cáº§u ká»¹ thuáº­t cá»‘t lÃµi | Commit xá»­ lÃ½ | CÃ¡ch tÃ¡i hiá»‡n & Báº±ng chá»©ng kiá»ƒm tra | Káº¿t luáº­n |
| :---: | :--- | :---: | :--- | :---: |
| **R-B01** | `CODEBOOK_V1.md` vÃ  `dictionary_v1.json` giá»¯ `pending_review`; CLI khÃ´ng ghi cá»©ng `codebook_version = 1.0.0`. | `7fe0239`<br>`6817d7e` | ÄÃ£ rÃ  soÃ¡t CLI: CLI Ä‘á»c Ä‘á»™ng tá»« metadata gÃ³i `package_meta` hoáº·c tham sá»‘ dÃ²ng lá»‡nh; khÃ´ng ghi cá»©ng 1.0.0. TÃ i liá»‡u váº«n giá»¯ `pending_review`. | **Äáº¡t** |
| **R-B02** | `compute_cohens_kappa` khÃ´ng Ä‘Æ°á»£c loáº¡i bá» toÃ n bá»™ ca khÃ³; pháº£i giá»¯ ca khÃ³ thuá»™c subset ngáº«u nhiÃªn. | `6817d7e` | Cháº¡y test case vá»›i 4 máº«u cÃ³ `random_subset=True`, trong Ä‘Ã³ 1 máº«u cÃ³ `difficult_case=True`. Káº¿t quáº£ `sample_count` Ä‘áº¡t Ä‘á»§ 4 máº«u. | **Äáº¡t** |
| **R-B03** | Kháº³ng Ä‘á»‹nh gÃ³i 20 máº«u ban Ä‘áº§u lÃ  fixture mÃ´ phá»ng; chuáº©n bá»‹ gÃ³i tháº­t 32 máº«u (20 ká»¹ thuáº­t + 12 phish). | `6817d7e` | ÄÃ£ táº¡o `scripts/data/build_real_pilot.py` vÃ  `configs/pilot_manifest.json` ghi nháº­n Ä‘áº§y Ä‘á»§ nguá»“n gá»‘c 20 API + 12 parquet. | **Äáº¡t** *(vá» kiáº¿n trÃºc)*<br>**ChÆ°a kiá»ƒm** *(dá»¯ liá»‡u thÃ´ C-only)* |
| **R-B04** | LÃ m rÃµ cÄƒn cá»© cá»­a sá»• Check Point 5 quÃ½ vÃ  ngÃ y káº¿t thÃºc táº­p train (08/09/2025); quy táº¯c temporal as-of. | `7fe0239`<br>`6817d7e` | Codebook má»¥c 1 vÃ  Dictionary Ä‘Ã£ ghi nháº­n `temporal_protocol_note` vÃ  giáº£i trÃ¬nh cá»­a sá»• Q4/2025. | **Äáº¡t** |
| **L-B01** | Kháº¯c phá»¥c cáº¯t cá»¥t vÄƒn báº£n 600 kÃ½ tá»±; cho phÃ©p xem toÃ n vÄƒn an toÃ n trong khi Ä‘á»“ng há»“ báº¥m giá» váº«n cháº¡y liÃªn tá»¥c. | `7fe0239`<br>`6817d7e` | Test `test_pagination_advances_and_full_text` Ä‘áº¡t. Há»— trá»£ phÃ­m `v` (toÃ n vÄƒn), `m` (tiáº¿n 600 kÃ½ tá»±), Ä‘á»“ng há»“ `time.perf_counter()` cháº¡y liÃªn tá»¥c. | **Äáº¡t** |
| **L-B02** | TÃ¡ch biá»‡t hoÃ n toÃ n dá»¯ liá»‡u dry-run; khÃ´ng cho ghi Ä‘Ã¨ vÃ o file nhÃ£n ngÆ°á»i hoáº·c lÃ m báº©n chá»‰ sá»‘ Kappa. | `7fe0239`<br>`6817d7e` | Dry-run tá»± Ä‘á»™ng Ä‘á»•i annotator thÃ nh `simulated_<id>`, xuáº¥t file `.dryrun.jsonl`, gÃ¡n `is_dry_run=True`; Kappa tá»± Ä‘á»™ng lá»c bá». Test kiá»ƒm tra cÃ¡ch ly Ä‘áº¡t. | **Äáº¡t** |
| **L-B03** | Resume pháº£i kiá»ƒm tra tÃ­nh tÆ°Æ¡ng thÃ­ch annotator, pass_id; phÃ¡t hiá»‡n trÃ¹ng ID; cáº¥m nháº§m láº«n annotator. | `7fe0239`<br>`6817d7e` | Test `test_load_already_annotated_sample_ids_rejects_rater_mismatch` Ä‘áº¡t. NÃ©m lá»—i náº¿u B trá» vÃ o file cá»§a A hoáº·c sai pass_id. | **Äáº¡t má»™t pháº§n** *(ChÆ°a kiá»ƒm package/hash)* |
| **L-B04** | KhÃ´ng Ã¢m tháº§m bá» qua (`pass`) cÃ¡c dÃ²ng JSONL bá»‹ há»ng; pháº£i bÃ¡o lá»—i kÃ¨m sá»‘ dÃ²ng cá»¥ thá»ƒ. | `7fe0239`<br>`6817d7e` | Test `test_load_already_annotated_sample_ids_rejects_malformed_json` Ä‘áº¡t. NÃ©m `ValueError` kÃ¨m vá»‹ trÃ­ dÃ²ng lá»—i. | **Äáº¡t** |
| **L-B05** | Loáº¡i bá» gÃ¡n cá»©ng `random_subset=True`; Ä‘á»c Ä‘á»™ng tá»« metadata gÃ³i; tá»« chá»‘i giÃ¡ trá»‹ kiá»ƒu chuá»—i. | `7fe0239`<br>`6817d7e` | Test `test_cli_reads_metadata_and_rejects_string_boolean` Ä‘áº¡t. Äá»c tá»« sample/package metadata, tá»« chá»‘i `"false"` (chuá»—i). | **Äáº¡t má»™t pháº§n** *(Cáº§n cháº·n CLI override lÆ°á»£t tháº­t)* |
| **L-B06** | Sá»­a cÃ´ng cá»¥ Cohen's Kappa: phÃ¢n biá»‡t ca khÃ³ ngáº«u nhiÃªn vá»›i ca khÃ³ chuyá»ƒn thÃªm; há»— trá»£ chá»n nhÃ£n lá»›p/tá»• chá»©c. | `6817d7e` | HÃ m `compute_cohens_kappa` lá»c theo `random_subset`; há»— trá»£ tham sá»‘ `label_field` (`class_label` hoáº·c `primary_org`). | **Äáº¡t** |

---

## 2. RÃ€ SOÃT CÃ”NG Cá»¤ COHEN'S KAPPA & Lá»ŒC MáºªU NGáºªU NHIÃŠN

### 2.1. Kiá»ƒm chá»©ng báº£o tá»“n ca khÃ³ trong máº«u ngáº«u nhiÃªn (Regression Test)
* **YÃªu cáº§u cá»§a Lead D:** Kiá»ƒm tra trÆ°á»ng há»£p 4 máº«u random cÃ³ 1 máº«u khÃ³ $\to$ káº¿t quáº£ pháº£i tÃ­nh Ä‘á»§ 4 máº«u vÃ o Cohen's Kappa.
* **Báº±ng chá»©ng thá»±c nghiá»‡m:**
  Äoáº¡n mÃ£ kiá»ƒm thá»­ Ä‘á»™c láº­p:
  ```python
  rater1 = [
      {"class_label": "phishing", "random_subset": True, "difficult_case": False},
      {"class_label": "benign",   "random_subset": True, "difficult_case": False},
      {"class_label": "phishing", "random_subset": True, "difficult_case": True},  # Ca khÃ³ ngáº«u nhiÃªn
      {"class_label": "benign",   "random_subset": True, "difficult_case": False},
  ]
  rater2 = [
      {"class_label": "phishing", "random_subset": True, "difficult_case": False},
      {"class_label": "benign",   "random_subset": True, "difficult_case": False},
      {"class_label": "benign",   "random_subset": True, "difficult_case": True},  # Báº¥t Ä‘á»“ng trÃªn ca khÃ³
      {"class_label": "benign",   "random_subset": True, "difficult_case": False},
  ]
  res = compute_cohens_kappa(rater1, rater2, is_difficult=[False, False, True, False])
  ```
  *Káº¿t quáº£:* `res.sample_count == 4`, `res.observed_agreement == 0.75`. Ca khÃ³ thá»© 3 Ä‘Æ°á»£c giá»¯ láº¡i hoÃ n toÃ n trong máº«u sá»‘. Náº¿u cÃ³ máº«u thá»© 5 vá»›i `random_subset=False` (ca khÃ³ chuyá»ƒn thÃªm), hÃ m sáº½ loáº¡i trá»« chÃ­nh xÃ¡c máº«u nÃ y.
* **Káº¿t luáº­n:** **Äáº T**.

### 2.2. Äiá»ƒm thiáº¿u sÃ³t cáº§n kháº¯c phá»¥c: Cáº·p máº«u Ä‘á»‘i chiáº¿u theo chá»‰ sá»‘ (Positional Zip)
* **Váº¥n Ä‘á» phÃ¡t hiá»‡n:** Trong `compute_cohens_kappa`, viá»‡c duyá»‡t cáº·p máº«u hiá»‡n táº¡i sá»­ dá»¥ng `zip(rater1, rater2)`.
* **Rá»§i ro:** HÃ m ngáº§m giáº£ Ä‘á»‹nh hai danh sÃ¡ch cÃ³ thá»© tá»± cÃ¡c máº«u hoÃ n toÃ n trÃ¹ng khá»›p. Náº¿u tá»‡p cá»§a A vÃ  B bá»‹ xÃ¡o trá»™n thá»© tá»± dÃ²ng (do máº¡ng, resume ngáº¯t quÃ£ng, hoáº·c lá»c máº«u), `zip` sáº½ ghÃ©p nháº§m máº«u A cá»§a ID nÃ y vá»›i máº«u B cá»§a ID khÃ¡c mÃ  khÃ´ng cáº£nh bÃ¡o.
* **YÃªu cáº§u Ä‘á»‘i vá»›i C:** HÃ m `compute_cohens_kappa` cáº§n há»— trá»£ Ä‘á»‘i chiáº¿u báº£n ghi theo `sample_id` (vÃ­ dá»¥ sá»­ dá»¥ng dictionary Ã¡nh xáº¡ `{sample_id: record}`) vÃ  kiá»ƒm tra xem cáº£ hai báº£n ghi cÃ³ cÃ¹ng xuáº¥t phÃ¡t tá»« má»™t phiÃªn báº£n gÃ³i dá»¯ liá»‡u (`package_id` / `package_hash`) hay khÃ´ng.
* **Káº¿t luáº­n:** **CHÆ¯A Äáº T** (Cáº§n bá»• sung Ä‘á»‘i chiáº¿u theo ID).

---

## 3. TÃCH Báº CH Dá»® LIá»†U MÃ” PHá»ŽNG VÃ€ Dá»® LIá»†U NGHIÃŠN Cá»¨U

* **Hiá»‡n tráº¡ng trong commit `6817d7e`:**
  * Lá»›p `AnnotationRecord` chá»‰ má»›i cÃ³ trÆ°á»ng `is_dry_run: bool = False`.
  * HoÃ n toÃ n thiáº¿u cÃ¡c trÆ°á»ng nguá»“n gá»‘c nghiÃªn cá»©u:
    - `is_synthetic: bool` (Ä‘Ã¡nh dáº¥u dá»¯ liá»‡u nhÃ¢n táº¡o hay trÃ­ch xuáº¥t tá»« web thá»±c táº¿)
    - `dataset_id: str` (mÃ£ Ä‘á»‹nh danh gÃ³i dá»¯ liá»‡u, vÃ­ dá»¥ `PRACTICE-PILOT-20` vs `REAL-PILOT-32-V1`)
    - `dataset_hash: str` (SHA-256 cá»§a tá»‡p Blind View Ä‘áº§u vÃ o)
    - `codebook_hash: str` (SHA-256 cá»§a Codebook Ä‘Æ°á»£c dÃ¹ng)
    - `sampling_plan_version: str` (phiÃªn báº£n káº¿ hoáº¡ch láº¥y máº«u)
* **Rá»§i ro nghiÃªm trá»ng:**
  Náº¿u má»™t thÃ nh viÃªn cháº¡y CLI trÃªn tá»‡p fixture `data/annotations/blind_view_pilot.json` (táº­p 20 máº«u mÃ´ phá»ng) **á»Ÿ cháº¿ Ä‘á»™ ngÆ°á»i tháº­t (khÃ´ng truyá»n `--dry-run`)**, CLI sáº½ sinh ra cÃ¡c báº£n ghi cÃ³:
  - `is_dry_run: False`
  - `seconds_spent`: thá»i gian ngÆ°á»i thao tÃ¡c tháº­t (vÃ­ dá»¥ 120 giÃ¢y)
  Tuy nhiÃªn, ná»™i dung vÄƒn báº£n vÃ  URL cá»§a cÃ¡c máº«u nÃ y lÃ  do láº­p trÃ¬nh viÃªn tá»± nghÄ© ra! Náº¿u sau Ä‘Ã³ cháº¡y script tá»•ng há»£p sá»‘ liá»‡u cho `PLAN-01` hoáº·c tÃ­nh Kappa, há»‡ thá»‘ng sáº½ coi Ä‘Ã¢y lÃ  nhÃ£n nghiÃªn cá»©u há»£p lá»‡.
* **YÃªu cáº§u Ä‘á»‘i vá»›i C:**
  1. Cáº­p nháº­t `AnnotationRecord` vÃ  schema xuáº¥t JSONL: Báº¯t buá»™c ghi nháº­n `is_synthetic`, `dataset_id`, `dataset_hash`, `codebook_hash`.
  2. Bá»• sung cÆ¡ cháº¿ trong cÃ¡c script bÃ¡o cÃ¡o nghiÃªn cá»©u vÃ  tÃ­nh Cohen's Kappa: **Tá»± Ä‘á»™ng tá»« chá»‘i (reject / exclude)** cÃ¡c báº£n ghi cÃ³ `is_synthetic == True` hoáº·c `dataset_id` thuá»™c danh má»¥c mock fixture.
* **Káº¿t luáº­n:** **CHÆ¯A Äáº T**.

---

## 4. TÃNH TOÃ€N Váº¸N Cá»¦A CÆ  CHáº¾ RESUME CLI

* **Äiá»ƒm Ä‘Ã£ hoÃ n thiá»‡n tá»‘t:**
  HÃ m `load_already_annotated_sample_ids()` Ä‘Ã£ kiá»ƒm tra nghiÃªm ngáº·t:
  - BÃ¡o lá»—i `MÃ‚U THUáºªN ÄÃNH GIÃ VIÃŠN` náº¿u file output chá»©a nhÃ£n cá»§a ngÆ°á»i khÃ¡c (`annotator_id != expected`).
  - BÃ¡o lá»—i `MÃ‚U THUáºªN LÆ¯á»¢T GÃN` náº¿u sai `pass_id`.
  - BÃ¡o lá»—i `Lá»–I Táº P NHIá»„M Dá»® LIá»†U` náº¿u file ngÆ°á»i tháº­t chá»©a báº£n ghi dry-run.
  - BÃ¡o lá»—i cÃº phÃ¡p JSON nÃªu rÃµ sá»‘ dÃ²ng vi pháº¡m; kiá»ƒm tra phÃ¡t hiá»‡n `sample_id` bá»‹ trÃ¹ng láº·p.
* **Äiá»ƒm thiáº¿u sÃ³t:**
  HÃ m **chÆ°a kiá»ƒm tra danh tÃ­nh vÃ  tÃ­nh toÃ n váº¹n cá»§a gÃ³i dá»¯ liá»‡u Ä‘áº§u vÃ o**:
  - Náº¿u ngÆ°á»i gÃ¡n nhÃ£n Ä‘Ã£ cháº¥m xong máº«u `PILOT-001` trÃªn gÃ³i `synthetic_pilot.json`. Sau Ä‘Ã³, C bÃ n giao gÃ³i `real_pilot.json` (cÅ©ng chá»©a mÃ£ `PILOT-001` nhÆ°ng ná»™i dung URL vÃ  vÄƒn báº£n hoÃ n toÃ n khÃ¡c).
  - Khi ngÆ°á»i dÃ¹ng cháº¡y CLI resume trÃªn file output cÅ©, CLI chá»‰ kiá»ƒm tra `sid in annotated` $\to$ bá» qua máº«u `PILOT-001` má»›i cá»§a gÃ³i tháº­t vÃ  coi nhÆ° Ä‘Ã£ hoÃ n thÃ nh!
* **YÃªu cáº§u Ä‘á»‘i vá»›i C:**
  Khi khá»Ÿi Ä‘á»™ng phiÃªn resume, CLI pháº£i kiá»ƒm tra tÃ­nh tÆ°Æ¡ng thÃ­ch giá»¯a header/metadata cá»§a tá»‡p output vÃ  tá»‡p input (`dataset_id`, `dataset_hash`, `codebook_version`). Náº¿u phÃ¡t hiá»‡n Ä‘á»•i gÃ³i dá»¯ liá»‡u hoáº·c Ä‘á»•i phiÃªn báº£n codebook, CLI pháº£i tá»« chá»‘i tiáº¿p tá»¥c vÃ  yÃªu cáº§u chá»‰ Ä‘á»‹nh tá»‡p output má»›i.
* **Káº¿t luáº­n:** **CHÆ¯A Äáº T** (Cáº§n bá»• sung kiá»ƒm tra gÃ³i khi resume).

---

## 5. CODEBOOK VÃ€ RÃ€NG BUá»˜C RANDOM MEMBERSHIP

* **Äá»c metadata Ä‘á»™ng:** Commit `6817d7e` Ä‘Ã£ loáº¡i bá» hoÃ n toÃ n viá»‡c gÃ¡n cá»©ng `random_subset=True` vÃ  `codebook_version="1.0.0"`. CLI Ä‘Ã£ Ä‘á»c theo thá»© tá»± Æ°u tiÃªn tá»« sample metadata vÃ  package metadata.
* **Váº¥n Ä‘á» quyá»n háº¡n dÃ²ng lá»‡nh:** CLI váº«n Ä‘ang duy trÃ¬ cá» `--random-subset` (`cli_random_subset`), cho phÃ©p ngÆ°á»i cháº¡y dÃ²ng lá»‡nh tá»± Ã½ ghi Ä‘Ã¨ giÃ¡ trá»‹ `random_subset` cá»§a tá»«ng máº«u.
  - *NguyÃªn táº¯c:* Trong cÃ¡c Ä‘á»£t gÃ¡n nhÃ£n nghiÃªn cá»©u chÃ­nh thá»©c, thuá»™c tÃ­nh `random_subset` lÃ  thuá»™c tÃ­nh phÆ°Æ¡ng phÃ¡p luáº­n cá»‘ Ä‘á»‹nh trong Sampling Manifest do C vÃ  Lead khÃ³a trÆ°á»›c khi má»Ÿ gÃ³i. NgÆ°á»i gÃ¡n nhÃ£n A vÃ  B tuyá»‡t Ä‘á»‘i khÃ´ng Ä‘Æ°á»£c tá»± Ã½ thay Ä‘á»•i cá» nÃ y qua tham sá»‘ CLI.
  - *YÃªu cáº§u:* Chá»‰ cho phÃ©p Ä‘á»c `random_subset` tá»« manifest/metadata cá»§a gÃ³i máº«u; vÃ´ hiá»‡u hÃ³a viá»‡c ghi Ä‘Ã¨ báº±ng cá» CLI trong cÃ¡c phiÃªn gÃ¡n nhÃ£n chÃ­nh thá»©c.
* **Tráº¡ng thÃ¡i Codebook:**
  - XÃ¡c nháº­n ThÃ nh viÃªn B (PhÃ¹ng Táº¥n Minh) Ä‘Ã£ nháº­n viá»‡c vÃ  rÃ  soÃ¡t ká»¹ thuáº­t.
  - Tuy nhiÃªn, `CODEBOOK_V1.md` vÃ  `configs/dictionary_v1.json` **tiáº¿p tá»¥c Ä‘Æ°á»£c giá»¯ á»Ÿ tráº¡ng thÃ¡i `pending_review`** cho Ä‘áº¿n khi C hoÃ n táº¥t chá»‰nh sá»­a cÃ¡c Ä‘iá»ƒm rÃ  soÃ¡t vÃ  Lead D chÃ­nh thá»©c kÃ½ duyá»‡t.
* **Káº¿t luáº­n:** **Äáº T Má»˜T PHáº¦N**.

---

## 6. RÃ€ SOÃT Tá»ª ÄIá»‚N 14 Tá»” CHá»¨C (DICTIONARY V1.0) & TEMPORAL AS-OF

ThÃ nh viÃªn B Ä‘Ã£ Ä‘á»‘i soÃ¡t Ä‘á»™c láº­p danh má»¥c 14 tá»• chá»©c trong `configs/dictionary_v1.json` vá»›i cÃ¡c bÃ¡o cÃ¡o Brand Phishing chÃ­nh thá»©c do Check Point Research (CPR) cÃ´ng bá»‘:

### 6.1. Báº£ng Ä‘á»‘i chiáº¿u nguá»“n gá»‘c vÃ  Ã¡nh xáº¡ danh má»¥c 5 quÃ½ (Q4/2024 â€“ Q4/2025)

| QuÃ½ kháº£o sÃ¡t | NgÃ y cÃ´ng bá»‘ | BÃ¡o cÃ¡o nguá»“n Check Point Research | ThÆ°Æ¡ng hiá»‡u gá»‘c trong Top 10 | Ãnh xáº¡ mÃ£ tá»• chá»©c (`org_id`) | Ghi chÃº & LÃ½ do Ä‘Æ°a vÃ o danh má»¥c |
| :---: | :---: | :--- | :--- | :---: | :--- |
| **Q4/2024** | 22/01/2025 | *Exploring Q4 2024 Brand Phishing Trends* | Microsoft (32%), Google (12%), Apple (12%), LinkedIn (11%), Amazon, Facebook, DHL | `microsoft`, `google`, `apple`, `linkedin`, `amazon`, `meta`, `dhl` | Microsoft dáº«n Ä‘áº§u; LinkedIn quay trá»Ÿ láº¡i top 4; DHL Ä‘áº¡i diá»‡n logistics mÃ¹a lá»… há»™i. |
| **Q1/2025** | 21/04/2025 | *Microsoft Dominates as Top Target... Mastercard Makes a Comeback* | Microsoft (36%), Google (12%), Apple (8%), Amazon, Mastercard, Facebook, PayPal | `mastercard`, `paypal` *(cÃ¹ng cÃ¡c hÃ£ng cÃ´ng nghá»‡)* | Mastercard tÃ¡i xuáº¥t hiá»‡n trong top tÃ i chÃ­nh; PayPal duy trÃ¬ táº§n suáº¥t cao. |
| **Q2/2025** | 22/07/2025 | *Phishing Trends Q2 2025... Spotify Re-enters as a Prime Target* | Microsoft (25%), Google (11%), Apple (9%), Amazon, Spotify, Facebook, Alibaba | `spotify`, `alibaba` | Spotify trá»Ÿ láº¡i top 10 láº§n Ä‘áº§u ká»ƒ tá»« 2019; Alibaba Ä‘áº¡i diá»‡n thÆ°Æ¡ng máº¡i Ä‘iá»‡n tá»­ quá»‘c táº¿. |
| **Q3/2025** | 16/10/2025 | *Microsoft Dominates Phishing Impersonations in Q3 2025* | Microsoft, Google, Apple, Amazon, Facebook, PayPal, Adobe | `adobe` | Adobe xuáº¥t hiá»‡n trong top vá»›i chiáº¿n dá»‹ch giáº£ máº¡o hÃ³a Ä‘Æ¡n PDF vÃ  pháº§n má»m Ä‘á»™c háº¡i. |
| **Q4/2025** | 15/01/2026 | *Microsoft Remains the Most Imitated Brand in Q4 2025* | Microsoft (22%), Google (13%), Amazon (9%), Facebook, Booking, Twitter | `booking`, `x_twitter` | Booking.com máº¡o danh du lá»‹ch cuá»‘i nÄƒm; Twitter (X) tiáº¿p tá»¥c bá»‹ lá»£i dá»¥ng tÃ i khoáº£n xÃ¡c minh. |

*Há»£p nháº¥t 5 quÃ½:* Cho ra chÃ­nh xÃ¡c **14 mÃ£ tá»• chá»©c duy nháº¥t** (`microsoft`, `google`, `meta`, `apple`, `amazon`, `linkedin`, `x_twitter`, `paypal`, `adobe`, `booking`, `dhl`, `spotify`, `alibaba`, `mastercard`).
*Cam káº¿t:* Danh má»¥c nÃ y Ä‘Æ°á»£c xÃ¡c láº­p hoÃ n toÃ n dá»±a trÃªn báº±ng chá»©ng Ä‘e dá»a thá»±c táº¿ tá»« nguá»“n nghiÃªn cá»©u Ä‘á»™c láº­p bÃªn ngoÃ i, **tuyá»‡t Ä‘á»‘i khÃ´ng Ä‘iá»u chá»‰nh danh má»¥c dá»±a trÃªn káº¿t quáº£ hay Ä‘á»™ chÃ­nh xÃ¡c cá»§a mÃ´ hÃ¬nh há»c mÃ¡y**.

### 6.2. Quy táº¯c TÃªn miá»n, Báº±ng chá»©ng Alias vÃ  Háº¡ táº§ng DÃ¹ng chung (UGC Hosting)
* **Quy táº¯c tiá»n nghiá»‡m UGC (Precedence Rule):**
  Quy táº¯c tÃªn miá»n trong `src/phishing/features/domains.py` Ä‘Ã£ Ã¡p dá»¥ng cÆ¡ cháº¿ duyá»‡t Æ°u tiÃªn: Má»i tÃªn miá»n thuá»™c danh sÃ¡ch UGC (`forms.office.com`, `sites.google.com`, `docs.google.com`, `drive.google.com`, `s3.amazonaws.com`, `*.blob.core.windows.net`, `*.firebaseapp.com`) **luÃ´n Ä‘Æ°á»£c gÃ¡n vai trÃ² `user_content_hosting` trÆ°á»›c**, báº¥t ká»ƒ thá»© tá»± khai bÃ¡o trong tá»« Ä‘iá»ƒn. KhÃ´ng bao giá» suy thÃ nh `first_party_identity`.
* **Quy táº¯c Temporal As-Of (ARS Lookahead Protection):**
  Dá»¯ liá»‡u táº­p train PhreshPhish thá»±c táº¿ káº¿t thÃºc vÃ o ngÃ y **08/09/2025** (thuá»™c Q3/2025). Do Ä‘Ã³, Ä‘á»‘i vá»›i bÃ i toÃ¡n Ä‘Ã¡nh giÃ¡ Temporal Split (RQ3), cÃ¡c bÃ¡o cÃ¡o cá»§a quÃ½ Q4/2025 (cÃ´ng bá»‘ ngÃ y 15/01/2026) **khÃ´ng Ä‘Æ°á»£c phÃ©p sá»­ dá»¥ng** Ä‘á»ƒ Ä‘á»‹nh nghÄ©a tá»« Ä‘iá»ƒn táº¡i cÃ¡c má»‘c huáº¥n luyá»‡n trÆ°á»›c ngÃ y 15/01/2026.
* **Káº¿t luáº­n:** **Äáº T**.

---

## 7. KIá»‚M Äá»ŠNH GÃ“I PILOT THáº¬T (REAL PILOT 32 MáºªU)

### 7.1. Cáº¥u trÃºc GÃ³i Pilot Tháº­t theo Manifest (`configs/pilot_manifest.json`)
* MÃ£ táº­p dá»¯ liá»‡u: `REAL-PILOT-32-V1`, `is_synthetic: false`.
* Quy mÃ´: **32 máº«u thá»±c táº¿**, bao gá»“m:
  * **20 máº«u ká»¹ thuáº­t:** KhÃ´i phá»¥c tá»« train API offset 0..19, khá»›p chÃ­nh xÃ¡c 100% mÃ£ bÄƒm lÆ°u trá»¯: `738ea69b920cb3037d7e9da38590024d8faa5f34c2eca6c760cb34690f2f190f` (8 phish, 12 benign).
  * **12 máº«u phishing bá»• sung:** Láº¥y tá»« shard Ä‘Ã£ khÃ³a `train-055.parquet` thuá»™c commit `eabec4b7a66324b79cc8a0ad856d1731dc26fe1a` (SHA-256: `205a7e1cf4fb11032683e90fdbd1c13ddc9d9dd86109658d13e69929b53b31d0`).
* TÃ¡ch biá»‡t thÃ´ng tin nhÃ£n: A vÃ  B chá»‰ nháº­n tá»‡p view mÃ¹ `data/annotations/blind_view_pilot_real.json` (chá»‰ cÃ³ URL, text, summary; hoÃ n toÃ n khÃ´ng cÃ³ source_label hay target). Tá»‡p mapping nhÃ£n nguá»“n `data/raw/pilot/source_mapping.json` Ä‘Æ°á»£c cÃ¡ch ly tuyá»‡t Ä‘á»‘i á»Ÿ phÃ­a ThÃ nh viÃªn C.
* CÆ¡ cháº¿ chá»‘t cháº·n CLI: Script `annotate_cli.py` Ä‘Ã£ cÃ i Ä‘áº·t cÆ¡ cháº¿ tá»± Ä‘á»™ng nÃ©m ngoáº¡i lá»‡ náº¿u phÃ¡t hiá»‡n `dataset_type == "real_pilot_pending_review"`, ngÄƒn cháº·n viá»‡c vÃ´ tÃ¬nh má»Ÿ phiÃªn gÃ¡n nhÃ£n ngÆ°á»i trÆ°á»›c khi cÃ³ nghiá»‡m thu cá»§a B vÃ  D.

### 7.2. PhÃ¡t hiá»‡n lá»—i phá»¥ thuá»™c mÃ´i trÆ°á»ng khi cháº¡y Test Suite (86 tests)
Khi ThÃ nh viÃªn B thiáº¿t láº­p mÃ´i trÆ°á»ng kiá»ƒm thá»­ cháº¡y suite kiá»ƒm tra toÃ n diá»‡n táº¡i commit `6817d7e`:
* **Lá»‡nh thá»±c thi:** `python -m pytest tests/ -q`
* **Káº¿t quáº£:** **84 passed, 2 failed** (trÃªn tá»•ng sá»‘ 86 tests vÃ  32 subtests).
* **NguyÃªn nhÃ¢n lá»—i:**
  2 tests trong `tests/test_label_fixes.py` bá»‹ lá»—i:
  1. `test_exclusion_hashes_and_domain_do_not_exclude_unrelated_records` $\to$ `ModuleNotFoundError: No module named 'tldextract'`
  2. `test_real_pilot_builder_rejects_changed_original_bytes` $\to$ `ModuleNotFoundError: No module named 'tldextract'`
* **PhÃ¢n tÃ­ch:** Trong module `src/phishing/data/exclusion.py` (dÃ²ng 131) vÃ  `scripts/data/build_real_pilot.py` (dÃ²ng 29), mÃ£ nguá»“n gá»i trá»±c tiáº¿p `import tldextract`. DÃ¹ thÆ° viá»‡n nÃ y Ä‘Ã£ Ä‘Æ°á»£c khai bÃ¡o trong `requirements.txt` (`tldextract==5.4.0`), nhÆ°ng náº¿u mÃ´i trÆ°á»ng mÃ¡y cá»§a thÃ nh viÃªn chÆ°a cÃ i Ä‘áº·t gÃ³i nÃ y thÃ¬ há»‡ thá»‘ng lá»c exclusion vÃ  builder pilot sáº½ gÃ£y ngay láº­p tá»©c.
* **YÃªu cáº§u Ä‘á»‘i vá»›i C & NhÃ³m:** Cáº§n rÃ  soÃ¡t cÆ¡ cháº¿ fallback an toÃ n hoáº·c Ä‘áº£m báº£o tÃ i liá»‡u hÆ°á»›ng dáº«n yÃªu cáº§u cÃ i Ä‘áº·t Ä‘áº§y Ä‘á»§ mÃ´i trÆ°á»ng áº£o trÆ°á»›c khi cháº¡y suite kiá»ƒm thá»­.
* **Káº¿t luáº­n:** **Äáº T Vá»€ Máº¶T THIáº¾T Káº¾ Dá»® LIá»†U**; **CHÆ¯A KIá»‚M TRá»ŒN Váº¸N RUNTIME DO THIáº¾U DEPENDENCY**.

---

## 8. Báº°NG CHá»¨NG THá»°C NGHIá»†M ÄÃƒ CHáº Y

1. **Kiá»ƒm tra Commit `ccdfdbb`:**
   - ÄÃ£ xÃ¡c minh bÃ¡o cÃ¡o cá»§a C: Suite 78 tests Ä‘áº¡t 100% trong mÃ´i trÆ°á»ng chuáº©n hÃ³a cá»§a C.
2. **Kiá»ƒm tra Commit `6817d7e`:**
   - ÄÃ£ dá»±ng mÃ´i trÆ°á»ng scratch Ä‘á»™c láº­p vÃ  cháº¡y kiá»ƒm thá»­ tá»± Ä‘á»™ng: 84/86 tests Ä‘áº¡t, 32 subtests Ä‘áº¡t.
   - ÄÃ£ xÃ¡c minh Ä‘á»™c láº­p 4 ká»‹ch báº£n há»“i quy trong `test_label_fixes.py`:
     + PhÃ¢n trang vÄƒn báº£n `v` / `m` hoáº¡t Ä‘á»™ng mÆ°á»£t mÃ , Ä‘á»“ng há»“ tÃ­nh giá» liÃªn tá»¥c.
     + File dry-run bá»‹ cÃ´ láº­p, khÃ´ng trá»™n vÃ o file nhÃ£n ngÆ°á»i.
     + CLI tá»« chá»‘i tá»‡p Ä‘áº§u ra khi phÃ¡t hiá»‡n dÃ²ng JSON bá»‹ lá»—i hoáº·c sai Ä‘Ã¡nh giÃ¡ viÃªn.
     + CÃ´ng cá»¥ Cohen's Kappa giá»¯ láº¡i Ä‘á»§ 4 máº«u khi cÃ³ 1 ca khÃ³ ngáº«u nhiÃªn.
3. **CÃ¡c pháº§n chÆ°a kiá»ƒm tra:**
   - ChÆ°a kiá»ƒm tra viá»‡c cháº¡y thá»±c táº¿ builder `build_real_pilot.py` trÃªn 2 tá»‡p nguá»“n nhá»‹ phÃ¢n gá»‘c (do cÃ¡c tá»‡p nÃ y náº±m á»Ÿ thÆ° má»¥c háº¡n cháº¿ `data/raw/pilot/` thuá»™c quyá»n quáº£n lÃ½ cá»§a C).
   - ChÆ°a cÃ³ dá»¯ liá»‡u nhÃ£n ngÆ°á»i thá»±c táº¿ trÃªn gÃ³i 32 máº«u.

---

## 9. Káº¾ HOáº CH BÃ€N GIAO & BÆ¯á»šC TIáº¾P THEO

### BÃ n giao cho ThÃ nh viÃªn C:
1. **Bá»• sung cÃ¡c trÆ°á»ng provenance vÃ o `AnnotationRecord` vÃ  CLI:**
   Bá»• sung `is_synthetic`, `dataset_id`, `dataset_hash`, `codebook_hash`, `sampling_plan_version` vÃ o cáº¥u trÃºc báº£n ghi JSON Lines.
2. **NÃ¢ng cáº¥p cÆ¡ cháº¿ Resume CLI:**
   Kiá»ƒm tra tÃ­nh tÆ°Æ¡ng thÃ­ch giá»¯a metadata tá»‡p output cÅ© vÃ  tá»‡p input má»›i (`dataset_id`, `dataset_hash`).
3. **NÃ¢ng cáº¥p Ä‘á»‘i chiáº¿u Cohen's Kappa:**
   Bá»• sung cÆ¡ cháº¿ khá»›p báº£n ghi A vÃ  B theo `sample_id` vÃ  cÃ¹ng `package_hash` thay vÃ¬ chá»‰ dÃ¹ng positional `zip`.
4. **KhÃ³a cá» `--random-subset` trong lÆ°á»£t tháº­t:**
   KhÃ´ng cho phÃ©p ngÆ°á»i gÃ¡n nhÃ£n can thiá»‡p cá» nÃ y qua dÃ²ng lá»‡nh.
5. **Äáº£m báº£o mÃ´i trÆ°á»ng cháº¡y:**
   CÃ i Ä‘áº·t Ä‘áº§y Ä‘á»§ `tldextract==5.4.0` Ä‘á»ƒ 86/86 unit test Ä‘á»u pass xanh.

### BÃ n giao cho Lead D:
1. Quyáº¿t Ä‘á»‹nh phÃª duyá»‡t cÃ¡c Ä‘iá»ƒm bá»• sung ká»¹ thuáº­t nÃ³i trÃªn cá»§a C.
2. Sau khi C hoÃ n táº¥t 5 Ä‘iá»ƒm ká»¹ thuáº­t vÃ  cung cáº¥p gÃ³i `REAL-PILOT-32-V1` hoÃ n chá»‰nh, Lead D chÃ­nh thá»©c phÃ¡t lá»‡nh má»Ÿ phiÃªn gÃ¡n nhÃ£n pilot tháº­t.
3. Khi cÃ³ lá»‡nh cá»§a Lead D, ThÃ nh viÃªn B sáº½ thá»±c hiá»‡n phiÃªn gÃ¡n nhÃ£n pilot Ä‘á»™c láº­p Ä‘áº§u tiÃªn, ghi nháº­n thá»i gian trung thá»±c vÃ  chuyá»ƒn sang bÆ°á»›c tÃ­nh Cohen's Kappa pilot.
