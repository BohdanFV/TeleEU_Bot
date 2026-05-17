from __future__ import annotations

from pathlib import Path


def send_log_file(app, chat_id: int) -> None:
    if not app.db.is_admin(chat_id):
        return
    log_file = app.settings.logs_dir / "general.log"
    if log_file.exists():
        with log_file.open("rb") as file:
            app.bot.send_document(chat_id, file)
    else:
        app.bot.send_message(chat_id, "Файл логів ще не створено.", disable_notification=True)


def send_status(app, message) -> None:
    now = app.now()
    text = "Program Status:"
    text += f"\nthread_notification_alive = {app.notification_thread.is_alive() if app.notification_thread else False}"
    text += f"\nthread_botpolling_alive = {app.polling_thread.is_alive() if app.polling_thread else False}"
    text += f"\ncurrent_bot_time = {now}"
    text += f"\ncurrent_server_time = {app.real_now()}"
    text += f"\nTest_mode = {app.settings.test_mode}"
    app.bot.send_message(message.chat.id, text, disable_notification=True)
