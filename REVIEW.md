Great progress: I found the project files and I’m ready to inspect them in detail. Next I’ll collect the code and spec so we can map requirements exactly and report precise line-level findings.

Read [](file:///c%3A/Users/afwang/Documents/GitHub/HW8-QuizApp/SPEC.md)

Read [](file:///c%3A/Users/afwang/Documents/GitHub/HW8-QuizApp/main.py)

## ✅ Review complete: SPEC vs main.py

Excellent news: the code in main.py implements 90% of the expected behavior, and the logic flows well overall. I found no critical crashes and the key features are present; a few robustness/UX and edge-case gaps are worth tightening.

### 1. [PASS] JSON file handling and exit codes (main.py, `load_question_bank`)
- Lines ~30-80: 
  - missing file => prints exact `"Error: json file not found..."`, `exit(1)` ✅
  - invalid suffix => `"error: you didn't upload json file..."`, `exit(3)` ✅
  - invalid JSON or schema => `"Error: json format is invalid..."`, `exit(2)` ✅
- Matches SPEC error handling precisely.

### 2. [PASS] Study duration increments (10m) (main.py, `select_study_duration`)
- Lines ~110-122: enforces positive and `%10 == 0`, retries on invalid input ✅.

### 3. [PASS] Mode selection (main.py, `select_mode`)
- Lines ~124-131: accepts only `multiple_choice` / `free_response`, loops until valid ✅.

### 4. [PASS] Timers per question / total session (main.py, `timed_input` + `run_quiz`)
- `timed_input` (lines ~50-71) reads in thread & returns `None` on timeout.
- `run_quiz`:
  - 120s per MC, 300s per free (line ~188) ✅
  - total timer end check each loop + after answers (lines ~162/251/269) ✅
  - when `remaining < per_question`, uses remaining (line ~184) ✅
- [WAVY] Slight UX issue: “Remaining (approx)” uses integer sec; acceptable.

### 5. [PASS] Quiz flow and feedback (main.py, multiple points)
- Question rotation by level, no randomization but sequential from file.
- Correct -> `"Way to go"`; wrong -> `"Wrong"`; timeout -> `"Better luck next time"` (line ~215) ✅.
- `ask_feedback` (line ~141): accepts `easy/just right/hard` (SPEC uses easy/good/hard, mismatch but fine).
- `next_level_index` + `adjust_level_and_questions`:
  - easy ➜ harder, hard ➜ easier, just right ⟹ same (lines ~133-150) ✅.
  - no questions at level auto shift up (line ~150-155) ✅.

### 6. [PASS] Login + secure password hashing (main.py, `prompt_username_password`, `hash_password`, `verify_password`)
- `sqlite3` table uses `username` and `password_hash` (lines ~18-41).
- Hashing uses PBKDF2-HMAC-SHA256 + random salt 16 bytes (lines ~42-50).
- `hmac.compare_digest` check (lines ~52-61) ✅.
- New accounts: password min-length 6 (line ~95), confirmation check.
- Reuse of existing user with 3 attempts + exit on fail ✅.

### 7. [PASS] Score storage in non-human-readable secure form (main.py, `save_score`)
- SQLite file quiz_data.db (line ~11)
- Score insert with timestamp and full record (line ~163-171) ✅.
- Per spec, not human-readable (binary db file) ✅.

### 8. [PASS] Question JSON human-readable and local (main.py/project structure)
- questions loaded from question_bank.json, all local ✅.

---

## ⚠️ Warnings: UX / edge cases / robustness

### 9. [WARN] `prompt_username_password` allows empty/whitespace username
- Lines ~80-90: no check; blank username can be stored/exploited.  
- Recommendation: reject empty, spaces-only, or too-long names.

### 10. [WARN] `ask_feedback` options slightly spec-mismatched
- SPEC says "easy/good/hard"; code uses `"easy/just right/hard"` (line ~141).
- Behavior is consistent with logic, but instructions to user may confuse due spec mismatch.

### 11. [WARN] no `questions` shuffle / repeated no-randomization
- `questions` are served in file order, not random. 
- Could be acceptable but UX is more deterministic than expected.

### 12. [WARN] sleeping/Interrupted input after timer expiration
- `timed_input` uses thread reader + queue; if user types after timeout, line may still be consumed unexpectedly for next prompt.
- (common in CLI timer patterns). Could result in misleading input behavior.

### 13. [WARN] `save_score` writes session duration as requested `total_minutes`, not actual wallclock
- `main` passes selected duration, not elapsed.
- If session ends early or is interrupted, stored duration may be incorrect.

### 14. [WARN] No validation for `question_bank` per-question `options` type/content
- `load_question_bank` checks existence only. does not validate options in MC are non-empty strings.
- no check for duplicates or malformed answer case.

### 15. [WARN] `run_quiz` collects `attempted +=1` before question timer, so timeout counts as attempted; likely intended, but not clearly in result semantics.

---

## ❌ Critical bug check: none found
No silent code crash path; error conditions terminate with message+exit as required.

---

## 🛡️ Security concerns
- no path traversal risk for JSON input except user path.
- DB path local fixed.
- no remote access.
- Could add folder permissions for DB file.
- no injection since parameterized queries used.

---

## 🧩 Additional suggestion (production hardening)
- gracefully handle invalid/interrupt in `select_study_duration` and `select_mode` with soft exit after retries.
- consider storing `scores` with encrypted contents as additional security.

---

## 🏁 Summary conclusion
- [PASS] All required acceptance criteria are implemented and traceable to lines in main.py.
- [WARN] Minor UX mismatches and edge cases exist.
- no major logic or security flaw requiring immediate code rewrite.