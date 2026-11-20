# Запуск в Docker

[← К README](../README.md)

Выполните из корня проекта:

```bash
docker build -t steel-pipeline .
docker run --rm -v "./artifacts:/output" steel-pipeline
```

Первая команда собирает образ, вторая запускает все расчёты на встроенных данных.
Результаты сохраняются в папке `artifacts` на компьютере.

- `-t steel-pipeline` — имя образа.
- `--rm` — удалить контейнер после завершения.
- `-v "./artifacts:/output"` — сохранить результаты из контейнера в локальную папку.
