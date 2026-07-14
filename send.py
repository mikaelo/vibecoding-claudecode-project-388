#!/usr/bin/env python3
"""Отправка сообщения в Telegram через Bot API.

Доступы берутся из переменных окружения (имена — как в KNOWLEDGE.md):
  TELEGRAM_BOT_TOKEN — токен бота (из @BotFather)
  TELEGRAM_CHAT_ID   — идентификатор чата/канала

Если переменные не заданы в окружении, скрипт подхватит их из файла .env
в той же директории. Секреты в репозиторий не коммитятся (.env в .gitignore).

Примеры:
  python3 send.py "Привет из tracker"
  echo "текст со stdin" | python3 send.py
  python3 send.py --chat-id 123456789 "в конкретный чат"
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def load_dotenv(path):
    """Подгружает KEY=VALUE из .env, не перезаписывая уже заданные переменные."""
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def send_message(token, chat_id, text):
    """Вызывает Telegram sendMessage. Возвращает разобранный JSON-ответ."""
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(API_URL.format(token=token), data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        # Telegram отдаёт JSON с описанием ошибки даже при 4xx.
        body = err.read().decode(errors="replace")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"ok": False, "error_code": err.code, "description": body}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Отправить сообщение в Telegram.")
    parser.add_argument("text", nargs="*", help="Текст сообщения (иначе — из stdin).")
    parser.add_argument("--chat-id", help="Переопределить TELEGRAM_CHAT_ID.")
    parser.add_argument("--token", help="Переопределить TELEGRAM_BOT_TOKEN.")
    args = parser.parse_args(argv)

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

    token = args.token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = args.chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        missing = ", ".join(
            name for name, val in (
                ("TELEGRAM_BOT_TOKEN", token), ("TELEGRAM_CHAT_ID", chat_id)
            ) if not val
        )
        sys.exit(f"Не заданы доступы: {missing}. Укажи их в .env или окружении.")

    if args.text:
        text = " ".join(args.text)
    else:
        text = sys.stdin.read().strip()
    if not text:
        sys.exit("Пустой текст сообщения — нечего отправлять.")

    result = send_message(token, chat_id, text)
    if result.get("ok"):
        msg = result.get("result", {})
        print(f"OK: сообщение {msg.get('message_id')} отправлено в чат {chat_id}")
        return 0
    print(
        "Ошибка отправки: "
        f"{result.get('error_code', '?')} {result.get('description', result)}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
