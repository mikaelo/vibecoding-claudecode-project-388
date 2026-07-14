# PROGRESS

Пайплайн отслеживания цен портфеля Финам, собранный из компонуемых Claude Code
skill'ов (директория `.claude/skills/`). Каждый шаг — отдельный skill; шаги
переиспользуют друг друга, а не дублируют логику.

## Схема пайплайна

```
extract_price  ──►  tracker  ──►  alert
 (1 тикер)         (снапшот         (сравнение с ценой
                    по счёту)        покупки + Telegram)
```

## Состояние шагов

| # | Skill           | Что делает                                                                                              | Источник данных                          | Статус |
|---|-----------------|---------------------------------------------------------------------------------------------------------|------------------------------------------|:------:|
| 1 | `extract_price` | Котировка одного тикера `TICKER@MIC` → `open`, `current` (last), `datetime`.                             | Finam MCP `get-quote`                    | ✅ |
| 2 | `tracker`       | По счёту резолвит позиции, по каждой вызывает `extract_price`, собирает snapshot (JSON+MD) и пишет его в репозиторий `mikaelo/tracker-data` файлом `YYYY-MM-DD-HH-MM.json`. | Finam MCP `get-accounts-list`, `get-account` + skill `extract_price`; GitHub MCP `create_or_update_file` | ✅ |
| 3 | `alert`         | По счёту сравнивает `current` с ценой покупки `averagePrice`, при отклонении ≥ порога (по умолчанию 10%, в любую сторону) шлёт сводку сработавших бумаг в Telegram. | Finam MCP `get-account` (averagePrice) + skill `extract_price` (current); Telegram Bot API `sendMessage` | ✅ |

## Ключевые решения

- **Переиспользование skill'ов.** `tracker` и `alert` берут текущую цену через
  `extract_price`, а не через `get-quote` напрямую. Цена покупки (`averagePrice`)
  доступна только из `get-account`.
- **Форма ответа `get-account` (Finam MCP).** Позиции — вложенные объекты:
  `positions[].symbol`, `positions[].averagePrice.value` (строка),
  `positions[].currentPrice.value` (строка). Значения-строки приводятся к числу.
- **Порог алерта.** Сравнивается модуль отклонения
  `(current − averagePrice) / averagePrice`; знак задаёт направление
  (`down`/`up`). По умолчанию `threshold=0.10`, `direction=both`.
- **Telegram.** Отправка через Bot API `sendMessage` (`curl`), доступы —
  `bot_token`/`chat_id` из входа или env `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`.
  Без доступов skill возвращает результат, но помечает `telegram.sent=false`.

## Проверено на реальных данных

Счёт `869168` (8 позиций). Для шага 3 при пороге 10% в обе стороны срабатывают
6 из 8 бумаг: BAZA (−16.7%), DGTL (−16.9%), SMLT (−63.7%), RENI (−11.5%) —
падение; OZON (+93.7%), LQDT (+54.9%) — рост. MOEX (−8.9%) и YDEX (−8.8%) ниже
порога и не срабатывают.

## Дальнейшие шаги (идеи)

- Обход нескольких счетов за один запуск (оркестрация поверх `tracker`/`alert`).
- Планировщик (cron) для регулярного снятия snapshot и алертов.
- Дедупликация алертов (не слать повторно, пока отклонение не изменилось).
