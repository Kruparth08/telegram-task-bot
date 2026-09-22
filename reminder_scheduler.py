import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_due_reminders, mark_reminder_sent

logger = logging.getLogger(__name__)

async def check_and_send_reminders(bot_app):
    try:
        due_reminders = get_due_reminders()
        for reminder in due_reminders:
            try:
                await bot_app.bot.send_message(
                    chat_id=reminder.user_id,
                    text=f"⏰ <b>REMINDER ALERT</b>\n\n{reminder.remind_message}",
                    parse_mode="HTML"
                )

                mark_reminder_sent(reminder.id)
                logger.info(f"Sent reminder {reminder.id} to user {reminder.user_id}")
            except Exception as e:
                logger.error(f"Failed to send reminder {reminder.id}: {e}")
    except Exception as e:
        logger.error(f"Error checking due reminders: {e}")

def start_scheduler(bot_app):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_send_reminders, 'interval', seconds=30, args=[bot_app])
    scheduler.start()
    logger.info("APScheduler background watchdog started.")
    return scheduler
