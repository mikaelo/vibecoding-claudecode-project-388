# PROGRESS — отслеживание цен акций Финам + Telegram

Документ-handoff для продолжения работы в новой сессии. Прочитай его целиком,
затем продолжай с раздела «Что дальше».

## Ветка

Вся работа — в ветке `claude/stock-price-telegram-alerts-b0luo8` репозитория
`mikaelo/vibecoding-claudecode-project-388`. Открывай/продолжай именно на ней.

## Цель проекта

Отслеживать позиции в портфелях брокера Финам и слать в Telegram уведомление,
если текущая цена акции отклонилась более чем на **10% от цены покупки**
(`averagePrice`). Шаги пайплайна (получение / хранение / сравнение данных)
реализуются как **Claude Code skills** в `.claude/skills/`, потому что данные
доступны только через MCP-инструменты внутри сессии Claude.

## Источники данных (проверено на живых данных)

- **Finam MCP** `get-accounts-list` → список счетов (`id`, `tradeCode`, `label`;
  `label` у всех пустой). `get-account(account_id)` → `positions[]` с полями
  `symbol` (формат `TICKER@MIC`), `quantity.value`, `averagePrice.value` (цена
  покупки), `currentPrice.value`. Часть счетов пустые или дают ошибку
  «Unknown account type» — их надо пропускать. Счёт с позициями для тестов:
  `869168` (8 бумаг: DGTL, BAZA, MOEX, OZON, SMLT, RENI, YDEX, LQDT).
- **Finam MCP** `get-quote(symbols)` → на элемент `items[0]`: `open` (цена
  открытия), `last` (текущая цена), `as_of` (время котировки, UTC). Ненайденный
  инструмент приходит как элемент с объектом `status` (`code`/`message`).
- **Telegram** — через **Upload-Post MCP** (`upload_text`,
  `platforms:["telegram"]`, `user:"Aventuristo"`). Подключён бот
  `TheExperimentQ25_bot` (профиль `Aventuristo`). Отдельного Telegram MCP нет.
- **GitHub** — операции через GitHub MCP (`mcp__github__*`).

## Реализованные skills

### `.claude/skills/extract_price/` — получение данных (готово)
Вход: `ticker` (`TICKER@MIC`, без `@` → `@MISX`). Выход:
`{ ticker, open, current, datetime }`. Вызывает `get-quote`. Проверен.

### `.claude/skills/tracker/` — сбор snapshot по счёту (готово)
Вход: `account` — ID **или** название/`tradeCode` счёта. Логика: резолв счёта
через `get-accounts-list` → позиции через `get-account` → по КАЖДОЙ бумаге
**вызывает skill `extract_price`** (инструмент Skill, не дублируя его логику) →
собирает snapshot `{ account_id, account_label, generated_at, rows[] }` (JSON +
Markdown). По факту формирования snapshot **пишет его в репозиторий
`mikaelo/tracker-data`**: файл в корне `YYYY-MM-DD-HH-MM.json` (UTC, из
`generated_at`) через `create_or_update_file` (всегда create, `sha` не нужен).
Проверен сбор snapshot на счёте `869168`.

## Открытый блокер: запись в `mikaelo/tracker-data`

Репозиторий `mikaelo/tracker-data` должен быть **в scope сессии** и доступен
GitHub App «Claude» на запись. В прошлой сессии он в scope не входил
(`not configured for this session`), а `add_repo` не подтверждался на web.
**Как решить:** создавать новую web-сессию, указав в источниках ОБА репозитория
(`vibecoding-claudecode-project-388` + `mikaelo/tracker-data`); убедиться, что
`tracker-data` существует и GitHub App имеет к нему доступ на запись.
Запасной вариант, если отдельный репо не нужен: писать снапшоты в текущий репо
в папку `snapshots/`.

## Что дальше

1. Добиться доступа к `mikaelo/tracker-data` (см. блокер) и проверить, что
   `tracker` реально создаёт файл `YYYY-MM-DD-HH-MM.json` в его корне.
2. Skill сравнения: по snapshot и `averagePrice` из `get-account` вычислить
   отклонение и отобрать бумаги с |Δ| > 10% от цены покупки.
3. Skill/шаг Telegram-уведомления: сформировать сообщение по отобранным бумагам
   и отправить через Upload-Post (`upload_text`, telegram, user `Aventuristo`).
4. (Опционально) оркестрация по всем счетам и запуск по расписанию.

## Открытые вопросы к пользователю

- Порог 10% — в обе стороны (рост и падение)? Скорее да (|Δ|).
- Хранение снапшотов: отдельный репо `tracker-data` или папка в текущем репо.
- Telegram: оставляем Upload-Post или прямой Bot API (token + chat_id).
- Набор отслеживаемых счетов: все с позициями или конкретные.
