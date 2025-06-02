import os
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook, DiscordEmbed

load_dotenv()
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")


def send_discord_notification(class_name, status, start_time, end_time):
    """
    Sends a notification to Discord via webhook.
    - class_name : the meeting or class name (e.g. "Maths")
    - status     : one of "joined", "left", or "noclass"
    - start_time : HH:MM when the meeting was supposed to start
    - end_time   : HH:MM when the meeting ends
    """
    if not WEBHOOK_URL:
        print("[x] DISCORD_WEBHOOK not found in .env")
        return

    webhook = DiscordWebhook(url=WEBHOOK_URL)

    # Choose color based on status
    color = '03b2f8'  # blue for joined
    if status == "left":
        color = 'f03c3c'  # red for left
    elif status == "noclass":
        color = 'f0a000'  # orange/yellow for no class

    embed = DiscordEmbed(
        title="Class Automation Update",
        color=color
    )
    embed.set_footer(text="MS Teams Bot • Swayam Tandon")
    embed.set_timestamp()

    embed.add_embed_field(name="Class (Meeting)", value=class_name, inline=True)
    embed.add_embed_field(name="Status", value=status.capitalize(), inline=True)
    embed.add_embed_field(name="Start Time", value=start_time, inline=True)
    embed.add_embed_field(name="End Time", value=end_time, inline=True)

    webhook.add_embed(embed)
    response = webhook.execute()

    if response.status_code in [200, 204]:
        print("[✔] Discord notification sent.")
    else:
        print(f"[x] Failed to send Discord message. Status: {response.status_code}")
