import os
import re
import sqlite3
import time
from datetime import datetime
from os import path

import schedule
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

from discord_notifier import send_discord_notification

# === Load credentials from .env ===
load_dotenv()
CREDS = {
    'email': os.getenv('EMAIL'),
    'passwd': os.getenv('PASSWORD')
}

# === Selenium Chrome options ===
opt = Options()
opt.add_argument("--disable-infobars")
opt.add_argument("--start-maximized")
opt.add_argument("--disable-extensions")
opt.add_argument("--no-sandbox")
opt.add_argument("--disable-dev-shm-usage")
opt.add_experimental_option("excludeSwitches", ["enable-automation"])
opt.add_experimental_option("prefs", {
    "profile.default_content_setting_values.media_stream_mic": 1,
    "profile.default_content_setting_values.media_stream_camera": 1,
    "profile.default_content_setting_values.geolocation": 1,
    "profile.default_content_setting_values.notifications": 1
})

driver = None
URL = "https://teams.microsoft.com/"

def createDB():
    """
    Creates (or verifies) the SQLite database with a timetable table that now has:
      - team_name    (e.g. "Team Rockers")
      - meeting_name (e.g. "Maths")
      - start_time   (HH:MM)
      - end_time     (HH:MM)
      - day          (monday, tuesday, etc.)
    """
    conn = sqlite3.connect('timetable.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS timetable(
        team_name TEXT,
        meeting_name TEXT,
        start_time TEXT,
        end_time TEXT,
        day TEXT
    )''')
    conn.commit()
    conn.close()
    print("Created (or verified) timetable Database")


def validate_input(regex, inp):
    """ Return True if `inp` matches the given regex pattern. """
    return bool(re.match(regex, inp))


def validate_day(inp):
    """ Return True if `inp` is one of monday, tuesday, ..., sunday """
    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    return inp.lower() in days


def add_timetable():
    """
    Prompts the user to add entries to the timetable.
    Now asks for:
      - Team Name    (e.g. "Team Rockers")
      - Meeting Name (e.g. "Maths")
      - Start Time   (HH:MM)
      - End Time     (HH:MM)
      - Day          (Monday/Tuesday/...)
    """
    if not path.exists("timetable.db"):
        createDB()

    while True:
        op = input("1. Add a meeting entry\n2. Done adding\nEnter option: ").strip()
        if op != "1":
            break

        team_name = input("Enter Team Name (e.g. Team Rockers): ").strip()
        while not team_name:
            print("Team Name cannot be blank.")
            team_name = input("Enter Team Name (e.g. Team Rockers): ").strip()

        meeting_name = input("Enter Meeting Name (e.g. Maths): ").strip()
        while not meeting_name:
            print("Meeting Name cannot be blank.")
            meeting_name = input("Enter Meeting Name (e.g. Maths): ").strip()

        start_time = input("Enter meeting start time (HH:MM, 24-hour): ").strip()
        while not validate_input(r"^\d\d:\d\d$", start_time):
            print("Invalid time format. Please use HH:MM.")
            start_time = input("Enter meeting start time (HH:MM, 24-hour): ").strip()

        end_time = input("Enter meeting end time (HH:MM, 24-hour): ").strip()
        while not validate_input(r"^\d\d:\d\d$", end_time):
            print("Invalid time format. Please use HH:MM.")
            end_time = input("Enter meeting end time (HH:MM, 24-hour): ").strip()

        day = input("Enter day of week (Monday/Tuesday/...): ").strip()
        while not validate_day(day):
            print("Invalid day. Choose from Monday, Tuesday, etc.")
            day = input("Enter day of week (Monday/Tuesday/...): ").strip()

        conn = sqlite3.connect('timetable.db')
        c = conn.cursor()
        c.execute("INSERT INTO timetable VALUES (?, ?, ?, ?, ?)",
                  (team_name, meeting_name, start_time, end_time, day.lower()))
        conn.commit()
        conn.close()
        print("Entry added!\n")


def view_timetable():
    """ Display all entries in the timetable database. """
    if not path.exists("timetable.db"):
        print("No timetable found. Please add classes first.")
        return

    conn = sqlite3.connect('timetable.db')
    c = conn.cursor()
    print("\nYour Timetable:")
    print("-" * 60)
    for row in c.execute('SELECT * FROM timetable ORDER BY day, start_time'):
        t_name, m_name, st, et, d = row
        print(f"Team: {t_name:15} | Meeting: {m_name:10} | {d.capitalize():9} {st}–{et}")
    print("-" * 60)
    conn.close()


def wait_for_login_or_app(driver, timeout=120):
    """
    Wait until either:
     - The login form (ID="i0116") appears, or
     - The main Teams app bar (CLASS_NAME="teams-app-bar") appears,
    whichever comes first, up to `timeout` seconds.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.any_of(
                EC.visibility_of_element_located((By.ID, "i0116")),
                EC.visibility_of_element_located((By.CLASS_NAME, "teams-app-bar"))
            )
        )
        print("Login form or Teams UI has loaded.")
    except Exception as e:
        print("Timed out waiting for Teams login or main UI:", e)
        driver.quit()
        exit(1)


def login():
    """
    After navigating to Teams, perform the Microsoft login:
     - Enter EMAIL → Next
     - Enter PASSWORD → Sign in
     - Possibly click “Stay signed in?”
    """
    global driver
    print("Logging in…")
    wait = WebDriverWait(driver, 60)
    try:
        # Email
        email_field = wait.until(EC.element_to_be_clickable((By.ID, "i0116")))
        email_field.clear()
        email_field.send_keys(CREDS['email'])
        wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()

        # Password
        password_field = wait.until(EC.element_to_be_clickable((By.ID, "i0118")))
        password_field.clear()
        password_field.send_keys(CREDS['passwd'])
        wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()

        # “Stay signed in?” prompt (sometimes appears)
        try:
            stay_btn = wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9")))
            stay_btn.click()
        except Exception:
            pass

        print("Login successful!")
    except Exception as e:
        print(f"Login failed: {e}")
        driver.quit()
        exit(1)


def joinclass(team_name=None, meeting_name=None, start_time=None, end_time=None):
    """
    1) If no `team_name`/`meeting_name` passed, look up the next upcoming meeting from the DB for today.
    2) Click on the correct Team card (using `team_name`).
    3) (No explicit channel click—assumes default/general channel is already open.)
    4) Locate the scheduled-meeting banner whose text contains `meeting_name`, and click its Join button.
       If not found, send a "noclass" notification.
    5) On the pre-join screen, turn off camera/mic (using the new checkbox toggle), click the final Join (and send "joined" notification).
    6) Sleep until end_time, then click Leave (and send "left" notification).
    """
    global driver
    wait = WebDriverWait(driver, 60)

    # Step 1: If no parameters passed, query the DB for the next meeting today
    if not team_name or not meeting_name or not start_time or not end_time:
        print("🔍 Looking for the next upcoming meeting today…")
        conn = sqlite3.connect('timetable.db')
        c = conn.cursor()

        now = datetime.now()
        today = now.strftime('%A').lower()
        current_time = now.strftime('%H:%M')

        query = """
            SELECT team_name, meeting_name, start_time, end_time
            FROM timetable
            WHERE day = ? AND start_time > ?
            ORDER BY start_time ASC
            LIMIT 1
        """
        c.execute(query, (today, current_time))
        result = c.fetchone()
        conn.close()

        if result:
            team_name, meeting_name, start_time, end_time = result
            print(f"✅ Next meeting: Team='{team_name}', Meeting='{meeting_name}' at {start_time}")
        else:
            print("✅ No more meetings scheduled for today.")
            return

    print(f"🎯 Joining '{meeting_name}' in Team '{team_name}'")

    # Step 2: Click the correct Team card on the left-hand pane
    try:
        # 2A) Wait until the Teams list is visible
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='team-name']"))
        )
        # 2B) Click the Team whose aria-label exactly matches `team_name`
        team_button = driver.find_element(
            By.CSS_SELECTOR,
            f"button[data-testid='team-name'][aria-label='{team_name}']"
        )
        print(f"⚙️ Clicking Team card: {team_name}")
        team_button.click()
        time.sleep(2)  # let the UI expand into that Team
    except Exception as e:
        print(f"❌ Could not click Team '{team_name}': {e}")
        return

    # Step 3: (Removed—assumes default/general channel is already open once the Team is clicked.)

    # Step 4: Look for the scheduled-meeting banner whose text contains `meeting_name`
    try:
        scheduled_meetings = driver.find_elements(
            By.XPATH,
            "//div[contains(@data-tid,'pre-state-schedule-meeting-banner-renderer')]"
        )
        if not scheduled_meetings:
            # Fallback: look for any <div> whose aria-label contains "Scheduled meeting"
            scheduled_meetings = driver.find_elements(
                By.XPATH,
                "//div[contains(@aria-label,'Scheduled meeting')]"
            )
    except Exception:
        scheduled_meetings = []

    if not scheduled_meetings:
        print(f"❌ Scheduled meeting for '{meeting_name}' not found.")
        send_discord_notification(meeting_name, "noclass", start_time, end_time)
        return

    banner_clicked = False
    for banner in scheduled_meetings:
        try:
            banner_text = banner.text or ""
            if meeting_name.lower() in banner_text.lower():
                print(f"📌 Found meeting banner for '{meeting_name}': \"{banner_text[:40]}…\"")
                # 4A) Click the Join button in that banner
                join_button = banner.find_element(
                    By.XPATH,
                    ".//button[@data-tid='pre-state-schedule-meeting-join-button']"
                )
                join_button.click()
                banner_clicked = True
                break
        except Exception:
            continue

    if not banner_clicked:
        print(f"❌ Scheduled meeting for '{meeting_name}' not found.")
        send_discord_notification(meeting_name, "noclass", start_time, end_time)
        return

    # Step 5: Wait for camera/mic pre-join screen to appear
    time.sleep(5)

    # Step 6: Turn off camera if it’s on (new checkbox toggle)
    try:
        cam_toggle = driver.find_element(By.CSS_SELECTOR, "div[data-tid='toggle-video']")
        if cam_toggle.get_attribute("aria-checked") == "true":
            cam_toggle.click()
    except Exception:
        pass

    # Step 6 (continued): Turn off mic if it’s on (new checkbox toggle)
    try:
        mic_toggle = driver.find_element(By.CSS_SELECTOR, "div[data-tid='toggle-mute']")
        if mic_toggle.get_attribute("aria-checked") == "true":
            mic_toggle.click()
    except Exception:
        pass

    # Step 7: Click the final "Join" (or "Join now") button
    try:
        join_now_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Join')]")
        join_now_btn.click()
        print(f"✅ Joined '{meeting_name}'.")
        send_discord_notification(meeting_name, "joined", start_time, end_time)
    except Exception:
        print("❌ ‘Join’ button on the pre-join screen was not found.")
        return

    # Step 8: Wait until end_time, then leave
    fmt = "%H:%M"
    class_duration = (datetime.strptime(end_time, fmt) - datetime.strptime(start_time, fmt)).seconds
    print(f"🕒 In meeting '{meeting_name}' for {class_duration // 60} minutes…")
    time.sleep(class_duration)

    # Step 9: Click "Leave"
    try:
        leave_btn = driver.find_element(By.XPATH, '//button[@aria-label="Leave"]')
        leave_btn.click()
        print(f"👋 Left '{meeting_name}'.")
        send_discord_notification(meeting_name, "left", start_time, end_time)
    except Exception:
        print("⚠️ Could not find the ‘Leave’ button. You may have to leave manually.")
        send_discord_notification(meeting_name, "left", start_time, end_time)


def start_browser():
    global driver
    driver = webdriver.Chrome(options=opt)
    driver.set_page_load_timeout(120)
    driver.get(URL)
    wait_for_login_or_app(driver, timeout=120)

    # If login is needed, do it
    if "login.microsoftonline.com" in driver.current_url or driver.find_elements(By.ID, "i0116"):
        login()
    else:
        print("Already logged in or Teams UI is visible.")


def sched():
    """
    Schedule each entry in the DB according to day and start_time.
    At the specified day/time, .do(joinclass, ...) will call joinclass()
    with the stored team_name, meeting_name, start_time, and end_time.
    """
    if not path.exists("timetable.db"):
        print("No timetable found. Please add meetings first.")
        return

    conn = sqlite3.connect('timetable.db')
    c = conn.cursor()
    for row in c.execute('SELECT * FROM timetable'):
        team_name, meeting_name, start_time, end_time, day = row
        day = day.lower()

        if day == "monday":
            schedule.every().monday.at(start_time).do(
                joinclass, team_name, meeting_name, start_time, end_time
            )
        elif day == "tuesday":
            schedule.every().tuesday.at(start_time).do(
                joinclass, team_name, meeting_name, start_time, end_time
            )
        elif day == "wednesday":
            schedule.every().wednesday.at(start_time).do(
                joinclass, team_name, meeting_name, start_time, end_time
            )
        elif day == "thursday":
            schedule.every().thursday.at(start_time).do(
                joinclass, team_name, meeting_name, start_time, end_time
            )
        elif day == "friday":
            schedule.every().friday.at(start_time).do(
                joinclass, team_name, meeting_name, start_time, end_time
            )
        elif day == "saturday":
            schedule.every().saturday.at(start_time).do(
                joinclass, team_name, meeting_name, start_time, end_time
            )
        elif day == "sunday":
            schedule.every().sunday.at(start_time).do(
                joinclass, team_name, meeting_name, start_time, end_time
            )

        print(f"Scheduled meeting '{meeting_name}' in Team '{team_name}' on {day.capitalize()} at {start_time}")

    conn.close()

    start_browser()
    print("Bot started. Waiting for scheduled meetings…")

    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        print("Bot stopped by user.")
        if driver:
            driver.quit()


if __name__ == "__main__":
    print("1. Modify Timetable\n2. View Timetable\n3. Start Bot")
    op = input("Enter option: ").strip()
    if op == "1":
        add_timetable()
    elif op == "2":
        view_timetable()
    elif op == "3":
        sched()
    else:
        print("Invalid option.")
