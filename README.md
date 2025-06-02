Microsoft Teams Online Class Automation Bot
Automate your Microsoft Teams class attendance with robust scheduling, Discord notifications, and camera/mic controls—all from your own timetable!

🎯 Features
Automated Login: Securely logs into Microsoft Teams using credentials from a .env file.

Custom Timetable: Interactive CLI to add, view, and manage your meeting/class schedule (team, meeting name, day, time).

Smart Meeting Join/Leave: Joins scheduled meetings at the right time, leaves automatically at the end.

Camera & Mic Control: Always joins meetings with camera and microphone OFF.

Discord Notifications: Sends status updates (joined, left, or not found) to your Discord channel via webhook.

SQLite Database: Stores your timetable securely and efficiently.

Robust Selenium Automation: Handles slow Teams loading and UI changes with explicit waits.

📸 Screenshots
Add screenshots here (e.g., login_success.png, meeting_joined.png) to show the bot in action!

⚙️ Setup Instructions
1. Clone the Repository
   text
   git clone https://github.com/yourusername/automation-bot.git
   cd automation-bot
2. Install Requirements
   text
   pip install -r requirements.txt
3. Configure Credentials
   Create a .env file in the project root:

text
EMAIL=your.email@domain.com
PASSWORD=your_password
DISCORD_WEBHOOK=https://discord.com/api/webhooks/your_webhook_id/your_webhook_token
4. Set Up ChromeDriver
   Download ChromeDriver matching your Chrome version.

Place it in your PATH or the project directory.

🚀 Usage
Modify Timetable:
Add your meetings/classes interactively.

text
python main.py
# Choose option 1 and follow prompts
View Timetable:
See your current schedule.

text
python main.py
# Choose option 2
Start the Bot:
The bot will automatically join/leave meetings as scheduled.

text
python main.py
# Choose option 3
📝 Example Timetable Entry
Team Name: Team Rockers

Meeting Name: Maths

Start Time: 10:00

End Time: 11:00

Day: Monday

🔔 Discord Notifications
Get instant updates in your Discord channel when the bot joins, leaves, or can’t find a meeting.

🛠️ File Structure
text
automation-bot/
├── main.py
├── discord_notifier.py
├── requirements.txt
├── .env
└── timetable.db  # (auto-created)
🧩 Customization
Add screenshots:
Use driver.save_screenshot("filename.png") in your code to capture proof of automation.

Change notification logic:
Edit discord_notifier.py for custom Discord messages or embeds.

❗ Troubleshooting
ModuleNotFoundError:
Install missing modules with pip install module-name.

ChromeDriver not found:
Ensure the driver matches your Chrome version and is in your PATH.

Bot not joining meetings:
Double-check your timetable, team/meeting names, and time format.

🙏 Credits
Inspired by tomassabol/MS-Teams-Attender-v2 and aniket328/microsoft-team-automation

Discord notifications via discord-webhook

Developed by Swayam Tandon

📜 License
MIT License

Enjoy your automated attendance! If you find this useful, star the repo and contribute!

