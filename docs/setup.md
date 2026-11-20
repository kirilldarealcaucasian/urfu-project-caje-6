# Локальный запуск

[← К README](../README.md) · [Docker](docker.md)

Из корня проекта (нужны uv и Python 3.13):

```bash
uv sync --locked
uv run --locked python .
```

- `sync` — установить зависимости и проект.
- `--locked` — использовать версии из `uv.lock` без его изменения.
- `python .` — запустить `__main__.py`.

Можно указать параметры:

```bash
uv run --locked python . --input data/raw/Steel_industry_data.csv --output-dir artifacts --save all
```

- `--input` — исходный CSV; по умолчанию файл из примера.
- `--output-dir` — папка результатов; без параметра результаты сохраняются в проекте.
- `--save` — что сохранить: `all` — всё, `tables` — таблицы, `figures` — графики, `processed` — подготовленные данные, `notebooks` — выполненные ноутбуки. Можно перечислить через запятую.

Форматирование кода:

```bash
uv run --locked ruff check --fix .
uv run --locked ruff format .
```

- `check --fix` — проверить код и исправить доступные замечания.
- `format` — отформатировать код.
- `.` — текущая папка проекта.
