# serverbot

`serverbot` — Telegram-бот для операционного управления сервером и фонового мониторинга.

Проект реализован как **модульный монолит** с двумя процессами:

- `bot` — принимает команды из Telegram, применяет ACL/аудит, запускает обработчики.
- `worker` — выполняет фоновые проверки и отправляет алерты.

---

## Содержание

- [Ключевые возможности](#ключевые-возможности)
- [Архитектура](#архитектура)
- [Структура проекта](#структура-проекта)
- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
- [Конфигурация](#конфигурация)
- [Команды Telegram](#команды-telegram)
- [RPZ workflow](#rpz-workflow)
- [ACL и аудит](#acl-и-аудит)
- [Логирование](#логирование)
- [Тестирование](#тестирование)
- [Roadmap](#roadmap)

---

## Ключевые возможности

- Telegram control-plane для операций:
  - системный статус;
  - Docker;
  - systemd;
  - журналы;
  - BIND;
  - RPZ;
  - ACL и аудит.
- Безопасный командный контур:
  - команды формируются через `CommandCatalog`;
  - аргументы валидируются;
  - применяется ACL-политика.
- Repository-backed workflow:
  - ACL и аудит через SQLite;
  - RPZ-правила через SQLite (`rpz_rules`) + `rndc reload <zone>` после мутаций.
- Грейсфул-шатдаун:
  - обработка `SIGINT` / `SIGTERM` у `bot` и `worker`.

---

## Архитектура

### Слои

1. **Domain**
   - модели, порты, ошибки;
   - протоколы репозиториев (`AuditRepository`, `PrincipalTagRepository`, `RpzRuleRepository`).
2. **Application**
   - use-cases/services/pipeline;
   - обработчики команд (`adapter_handlers`, `ops_adapter_handlers`);
   - `RpzService` для полного цикла add/del/list/find.
3. **Infrastructure**
   - Telegram gateway/controllers;
   - KDL loaders;
   - SQLite-адаптеры;
   - subprocess runner;
   - command catalog.

### Процессы

- `src/serverbot/main_bot.py` — polling Telegram, ACL/pipeline, обработка команд.
- `src/serverbot/main_worker.py` — periodic checker loop для alerting.

---

## Структура проекта

```text
.
├─ commands/                  # production command descriptors (*.kdl), по 1 команде в файле
│  ├─ example.kdl            # минимальный пример формата (исключён из production-loading)
│  ├─ status.kdl
│  ├─ docker.kdl
│  ├─ services.kdl
│  ├─ logs.kdl
│  ├─ bind.kdl
│  ├─ rpz.kdl
│  ├─ acl.kdl
│  ├─ audit.kdl
│  ├─ whoami.kdl
│  └─ exec.kdl
├─ config/
│  └─ serverbot.kdl          # runtime configuration
├─ src/serverbot/
│  ├─ main_bot.py
│  ├─ main_worker.py
│  ├─ domain/
│  ├─ application/
│  └─ infrastructure/
└─ tests/
```

---

## Требования

- Python `3.12+`
- Linux-host (для system-level команд типа `systemctl`, `journalctl`, `rndc`)
- Telegram Bot token

### Зависимости (минимум)

Указаны в `pyproject.toml`:

- `aiogram`
- `rich`
- dev: `pytest`

---

## Быстрый старт

### 1) Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 2) Конфигурация

Отредактируйте `config/serverbot.kdl` под ваш environment:

- telegram token;
- db path;
- allowlist units/zones;
- alert settings.

### 3) Запуск bot процесса

```bash
python -m serverbot.main_bot
```

### 4) Запуск worker процесса

```bash
python -m serverbot.main_worker
```

---

## Конфигурация

### Runtime KDL

- Основной runtime config: `config/serverbot.kdl`
- Загрузка через `KdlConfigLoader` + `ConfigService`.

### Command KDL

- Production команды читаются из директории `commands/`.
- Загружаются **все `commands/*.kdl`, кроме `commands/example.kdl`**.
- В каждом production-файле — одна root-команда (`name "..."`) и её subcommands.

---

## Команды Telegram

Команды описаны в `commands/*.kdl` и исполняются через command pipeline.

### Основные группы

- `/status`, `/status full`
- `/docker ls|ps|ps-all|inspect|restart|stop|start`
- `/services status|restart|reload`
- `/logs unit|docker`
- `/bind checkconf|checkzone|reconfig|reload|reload-zone|flush`
- `/rpz list|add|del|find`
- `/acl list|add-user|add-chat|grant|revoke`
- `/audit last`
- `/whoami`
- `/exec bind_reload|journal_unit|named_checkzone`

> Примечание: командный parser поддерживает subcommand-вызовы вроде `/docker ls` (subcommand попадает в `raw_tokens`).

---

## RPZ workflow

RPZ реализован как repository-backed контур:

1. Вход команды (`/rpz add ...` или `/rpz del ...`) попадает в `OpsAdapterCommandHandler`.
2. Вызов делегируется в `RpzService`.
3. `RpzService`:
   - валидирует аргументы;
   - пишет в `RpzRuleRepository` (`SqliteRpzRuleRepository`);
   - выполняет `rndc reload <zone>` через `CommandRunner`.

SQLite таблица: `rpz_rules(zone, qname, policy, value)`.

---

## ACL и аудит

- ACL хранится в `principal_tags`.
- Аудит команд — в `audit_log`.
- Если база ACL пуста, **первый пользователь, который отправит `/start`, автоматически получает полный набор прав администратора** (все теги зарегистрированных команд).
- Проверка доступа:
  - в pipeline вычисляется policy по required tag;
  - при deny возвращается `Access denied`;
  - факт вызова фиксируется в audit.

---

## Логирование

- Используется стандартный `logging`.
- Конфигурация: `src/serverbot/config/logging.py`.
- Verbose/non-verbose режим задаётся runtime config.

---

## Тестирование

Базовый запуск:

```bash
pytest -q
```

Полезные срезы:

```bash
pytest -q tests/unit/config
pytest -q tests/unit/application/commanding
pytest -q tests/integration/commanding
pytest -q tests/integration/db
```

---

## Roadmap

- Расширить dependency list в `pyproject.toml` до полного production-набора.
- Добавить explicit migration tooling для SQLite схем.
- Добавить e2e тесты Telegram update/callback flow.
- Подготовить docker-compose профиль для локальной dev-среды.
