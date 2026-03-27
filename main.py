import json
import os
import sys
import time
import sqlite3
import getpass
import hashlib
import hmac
import secrets
import threading
import queue
import datetime
import random
from pathlib import Path

if os.name == "nt":
    import msvcrt
else:
    import select

DATA_DIR = Path(__file__).resolve().parent
DEFAULT_QUESTION_BANK = DATA_DIR / "question_bank.json"
DB_PATH = DATA_DIR / "quiz_data.db"

LEVELS = ["easy", "medium", "hard"]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            mode TEXT NOT NULL,
            total_questions INTEGER NOT NULL,
            correct_answers INTEGER NOT NULL,
            duration_minutes INTEGER NOT NULL,
            FOREIGN KEY(username) REFERENCES users(username)
        )
        """
    )
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000)
    return f"{salt}:{dk.hex()}"


def verify_password(stored_hash: str, password: str) -> bool:
    try:
        salt, hashed = stored_hash.split(":")
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000).hex()
    return hmac.compare_digest(candidate, hashed)


def load_question_bank(filepath: str):
    file_path = Path(filepath)
    if not file_path.exists():
        print("Error: json file not found. please create bank and exit with code 1")
        sys.exit(1)
    if file_path.suffix.lower() != ".json":
        print("error: you didn't upload json file, this isn't going to work exit with code 3")
        sys.exit(3)
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("Error: json format is invalid. please fix it and exit with code 2")
        sys.exit(2)
    if not isinstance(data, dict) or "questions" not in data or not isinstance(data["questions"], list):
        print("Error: json format is invalid. please fix it and exit with code 2")
        sys.exit(2)

    questions = []
    for idx, q in enumerate(data["questions"]):
        if not isinstance(q, dict):
            print("Error: json format is invalid. please fix it and exit with code 2")
            sys.exit(2)
        required = ["question", "type", "answer", "level"]
        if any(key not in q for key in required):
            print("Error: json format is invalid. please fix it and exit with code 2")
            sys.exit(2)

        if not isinstance(q["question"], str) or not q["question"].strip():
            print("Error: json format is invalid. please fix it and exit with code 2")
            sys.exit(2)
        if not isinstance(q["answer"], str) or not q["answer"].strip():
            print("Error: json format is invalid. please fix it and exit with code 2")
            sys.exit(2)

        qtype = q["type"].strip().lower() if isinstance(q["type"], str) else ""
        if qtype not in ["multiple_choice", "free_response"]:
            print("Error: json format is invalid. please fix it and exit with code 2")
            sys.exit(2)

        level = q["level"].strip().lower() if isinstance(q["level"], str) else ""
        if level not in LEVELS:
            print("Error: json format is invalid. please fix it and exit with code 2")
            sys.exit(2)

        if qtype == "multiple_choice":
            options = q.get("options")
            if not isinstance(options, list) or len(options) < 2:
                print("Error: json format is invalid. please fix it and exit with code 2")
                sys.exit(2)
            if not all(isinstance(opt, str) and opt.strip() for opt in options):
                print("Error: json format is invalid. please fix it and exit with code 2")
                sys.exit(2)
            if q["answer"].strip() not in [opt.strip() for opt in options]:
                print("Error: json format is invalid. please fix it and exit with code 2")
                sys.exit(2)
            q["options"] = [opt.strip() for opt in options]

        q["question"] = q["question"].strip()
        q["answer"] = q["answer"].strip()
        q["type"] = qtype
        q["level"] = level

        questions.append(q)
    if len(questions) == 0:
        print("Error: json format is invalid. please fix it and exit with code 2")
        sys.exit(2)
    return questions


def timed_input(prompt: str, timeout_seconds: int):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    if os.name == "nt":
        result = ""
        start = time.time()
        while time.time() - start < timeout_seconds:
            if msvcrt.kbhit():
                ch = msvcrt.getwche()
                if ch in "\r\n":
                    print("")
                    return result
                if ch == "\b":
                    if result:
                        result = result[:-1]
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                else:
                    result += ch
            time.sleep(0.01)
        print("")
        return None
    else:
        rlist, _, _ = select.select([sys.stdin], [], [], timeout_seconds)
        if rlist:
            line = sys.stdin.readline()
            if line is None:
                return None
            return line.rstrip("\n")
        return None


def get_hidden_password(prompt: str) -> str:
    sys.stdout.write(prompt)
    sys.stdout.flush()
    password = ""
    while True:
        ch = msvcrt.getwch()
        if ch in "\r\n":
            print("")
            return password
        elif ch == "\b":
            if password:
                password = password[:-1]
                sys.stdout.write("\b \b")
                sys.stdout.flush()
        else:
            password += ch
            sys.stdout.write("*")
            sys.stdout.flush()


def prompt_username_password():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    while True:
        username = input("Username: ").strip()
        if not username:
            print("Username cannot be empty. Please enter a valid username.")
            continue
        if len(username) > 150:
            print("Username too long (max 150 characters).")
            continue
        break

    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    if row:
        attempts = 3
        while attempts > 0:
            password = get_hidden_password("Password: ")
            if verify_password(row[0], password):
                print("Login successful")
                conn.close()
                return username
            attempts -= 1
            print(f"Invalid password. {attempts} attempt(s) left.")
        print("Too many failed attempts. Exiting.")
        conn.close()
        sys.exit(1)
    else:
        print("No account found. Creating a new user.")
        while True:
            password = get_hidden_password("New password: ")
            confirm = get_hidden_password("Confirm password: ")
            if password != confirm:
                print("Passwords do not match. try again.")
            elif len(password) < 6:
                print("Password too short (min 6 chars).")
            else:
                break
        hashed = hash_password(password)
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed))
        conn.commit()
        conn.close()
        print("User created and logged in")
        return username


def select_study_duration():
    while True:
        choice = input("How many minutes do you want to study? (5, 10, 15, ...): ").strip()
        if not choice.isdigit():
            print("Enter a number in increments of 5.")
            continue
        mins = int(choice)
        if mins > 0 and mins % 5 == 0:
            return mins
        print("Enter a number in increments of 5.")


def select_mode():
    while True:
        choice = input("Choose mode (multiple_choice/free_response): ").strip().lower()
        if choice in ["multiple_choice", "free_response"]:
            return choice
        print("Invalid mode")


def filter_questions(questions, mode):
    return [q for q in questions if q["type"] == mode]


def next_level_index(current, feedback):
    if feedback == "easy":
        return min(len(LEVELS) - 1, current + 1)
    if feedback == "hard":
        return max(0, current - 1)
    # good = stay at same difficulty
    return current


def ask_feedback():
    while True:
        fb = input("Feedback (easy/good/hard): ").strip().lower()
        if fb in ["easy", "good", "hard"]:
            return fb
        print("Please type easy, good, or hard.")


def adjust_level_and_questions(level_idx, available, feedback):
    if feedback == "good":
        return level_idx
    new_index = next_level_index(level_idx, feedback)
    # if no questions at level and we are not at end, step up
    if len(available[LEVELS[new_index]]) == 0:
        if new_index < len(LEVELS) - 1:
            new_index += 1
    return new_index


def save_score(username, mode, total_q, correct_q, duration_mins):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO scores (username, timestamp, mode, total_questions, correct_answers, duration_minutes) VALUES (?, ?, ?, ?, ?, ?)",
        (username, datetime.datetime.utcnow().isoformat(), mode, total_q, correct_q, duration_mins),
    )
    conn.commit()
    conn.close()


def run_quiz(questions, mode, total_minutes):
    available = {level: [q for q in questions if q["level"] == level] for level in LEVELS}
    for lst in available.values():
        random.shuffle(lst)
    if all(len(lst) == 0 for lst in available.values()):
        print("No questions available for your mode/levels.")
        return 0, 0

    current_level_idx = 0
    # find first non-empty
    while current_level_idx < len(LEVELS) and not available[LEVELS[current_level_idx]]:
        current_level_idx += 1
    if current_level_idx >= len(LEVELS):
        print("No questions available for selected mode.")
        return 0, 0

    total_seconds = total_minutes * 60
    start_time = time.time()
    correct = 0
    attempted = 0
    presented = 0

    while True:
        elapsed = time.time() - start_time
        remaining = total_seconds - elapsed
        if remaining <= 0:
            print("Overall time is up!")
            break

        level = LEVELS[current_level_idx]
        if not available[level]:
            # move to next level
            found = False
            for li in range(current_level_idx + 1, len(LEVELS)):
                if available[LEVELS[li]]:
                    current_level_idx = li
                    level = LEVELS[current_level_idx]
                    found = True
                    break
            if not found:
                # no more questions in the higher levels, try going lower
                for li in range(0, current_level_idx):
                    if available[LEVELS[li]]:
                        current_level_idx = li
                        level = LEVELS[current_level_idx]
                        found = True
                        break
            if not found:
                print("No more questions available.")
                break

        # serve one question
        question = available[level].pop(0)
        presented += 1
        per_question = 120 if mode == "multiple_choice" else 300
        if remaining < per_question:
            per_question = int(remaining)
        print(f"\nLevel: {level} | Question {presented} | Remaining (approx): {int(remaining)} sec")
        print(question["question"])
        user_answer = None

        if mode == "multiple_choice":
            for i, opt in enumerate(question.get("options", []), 1):
                print(f"  {i}. {opt}")
            user_answer = timed_input(f"Answer (choice text or number) [{per_question} sec]: ", per_question)
        else:
            user_answer = timed_input(f"Answer (free response) [{per_question} sec]: ", per_question)

        if user_answer is None:
            print("Better luck next time")
            feedback = ask_feedback()
            current_level_idx = adjust_level_and_questions(current_level_idx, available, feedback)
            # time consumed
            if time.time() - start_time >= total_seconds:
                break
            continue

        attempted += 1
        user_answer = user_answer.strip()
        correct_answer = question["answer"].strip()

        is_correct = False
        if mode == "multiple_choice":
            qopts = question.get("options", [])
            if user_answer.isdigit():
                idx = int(user_answer) - 1
                if 0 <= idx < len(qopts) and qopts[idx].strip().lower() == correct_answer.lower():
                    is_correct = True
            if user_answer.strip().lower() == correct_answer.lower():
                is_correct = True
        else:
            if user_answer.strip().lower() == correct_answer.lower():
                is_correct = True

        if is_correct:
            print("Way to go")
            correct += 1
        else:
            print("Wrong")

        feedback = ask_feedback()
        current_level_idx = adjust_level_and_questions(current_level_idx, available, feedback)

        if time.time() - start_time >= total_seconds:
            print("Overall time is up!")
            break

    elapsed_seconds = time.time() - start_time
    return attempted, correct, elapsed_seconds


def main():
    init_db()

    bank_path = input(f"Enter path to question bank JSON file [{DEFAULT_QUESTION_BANK}]: ").strip() or str(DEFAULT_QUESTION_BANK)
    questions = load_question_bank(bank_path)

    username = prompt_username_password()

    mode = select_mode()
    total_minutes = select_study_duration()

    selected_questions = filter_questions(questions, mode)
    if not selected_questions:
        print("No questions available for chosen mode.")
        sys.exit(1)

    print("Starting quiz...")
    attempted, correct, elapsed_seconds = run_quiz(selected_questions, mode, total_minutes)
    duration_mins = max(1, int((elapsed_seconds + 59) // 60))

    print(f"\nSession complete. You answered {correct} out of {attempted} correctly.")
    choice = input("Save result? (yes/no): ").strip().lower()
    if choice == "yes":
        save_score(username, mode, attempted, correct, duration_mins)
        print("Saved.")
    else:
        print("Results not saved.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        sys.exit(0)
