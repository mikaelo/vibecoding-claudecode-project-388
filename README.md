### Hexlet tests and linter status:
[![Actions Status](https://github.com/mikaelo/vibecoding-claudecode-project-388/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/mikaelo/vibecoding-claudecode-project-388/actions)

## Пайплайн отслеживания цен портфеля Финам

Компонуемые Claude Code skill'ы (`.claude/skills/`): `extract_price` → `tracker`
→ `telegram_alert`. Все настройки — в [`KNOWLEDGE.md`](./KNOWLEDGE.md).

### Отправка в Telegram

Скрипт `send.py` шлёт сообщение через Telegram Bot API. Доступы берутся из
`.env` (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) — файл в `.gitignore`, шаблон в
`.env.example`.

```bash
python3 send.py "текст сообщения"
```

**Доступ к сети в облаке.** В облачной сессии Claude Code `api.telegram.org` по
умолчанию (Network access = **Trusted**) заблокирован. Чтобы `send.py` работал из
облака: в настройках окружения выбери **Network access → Custom**, добавь в
**Allowed domains** хост `api.telegram.org`, отметь галочку сохранения дефолтных
хостов и открой **новую** сессию. Локально/в CI это не требуется.