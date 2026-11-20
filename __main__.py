"""Запуск всех ноутбуков"""

import argparse
import os
import shutil
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent

NOTEBOOK_PATHS: tuple[str, ...] = (
    "eda/01_data_analysis.ipynb",
    "eda/01b_visual_analysis.ipynb",
    "validation/02_validation.ipynb",
    "modeling/03_baselines.ipynb",
    "modeling/04_optimization.ipynb",
)


ARTIFACTS = {
    "tables": "results/tables",
    "figures": "results/figures",
    "processed": "data/processed",
    "notebooks": "notebooks",
}
NOTEBOOK_DIRS = ("eda", "validation", "modeling")


def run_notebooks(workspace: Path) -> None:
    """Последовательно выполнить все этапы исследования."""

    for notebook_relative_path in NOTEBOOK_PATHS:
        notebook_path = workspace / notebook_relative_path
        print(f"Запуск {notebook_relative_path}", flush=True)
        notebook = nbformat.read(notebook_path, as_version=4)
        NotebookClient(
            notebook,
            timeout=1800,
            kernel_name="python3",
            resources={"metadata": {"path": str(workspace)}},
        ).execute()
        nbformat.write(notebook, notebook_path)
        print(f"Готово: {notebook_relative_path}", flush=True)


def parse_arguments() -> tuple[argparse.Namespace, set[str]]:
    """Прочитать параметры запуска и проверить входной файл и выбор результатов."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=os.environ.get("OUTPUT_DIR"),
        help="Папка выгрузки результатов (по умолчанию текущий проект)",
    )
    parser.add_argument(
        "--save",
        default=os.environ.get("SAVE", "all"),
        help="Через запятую: tables,figures,processed,notebooks; либо all",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/raw/Steel_industry_data.csv",
        help="Исходный CSV в формате Steel industry",
    )
    args = parser.parse_args()
    selected = {item.strip() for item in args.save.split(",")}
    if selected == {"all"}:
        selected = set(ARTIFACTS)
    if not selected <= ARTIFACTS.keys():
        parser.error("--save: допустимы tables,figures,processed,notebooks или all")
    if not args.input.is_file():
        parser.error(f"Исходный CSV не найден: {args.input}")
    return args, selected


def prepare_output_directory(output: Path) -> None:
    """Создать папку результатов и проверить возможность записи до запуска."""
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile(dir=output):
        pass


def prepare_workspace(workspace: Path, input_file: Path) -> None:
    """Скопировать код, ноутбуки и выбранный CSV во временную папку."""
    shutil.copytree(ROOT / "src", workspace / "src")
    for directory in NOTEBOOK_DIRS:
        shutil.copytree(ROOT / directory, workspace / directory)
    raw_dir = workspace / "data/raw"
    raw_dir.mkdir(parents=True)
    shutil.copy2(input_file, raw_dir / "Steel_industry_data.csv")


def save_results(workspace: Path, output: Path, selected: set[str]) -> None:
    """Выгрузить выбранные результаты, сохраняя структуру каталогов."""
    for kind in selected:
        if kind == "notebooks":
            for directory in NOTEBOOK_DIRS:
                shutil.copytree(
                    workspace / directory,
                    output / "notebooks" / directory,
                    dirs_exist_ok=True,
                )
        else:
            relative_path = ARTIFACTS[kind]
            shutil.copytree(
                workspace / relative_path,
                output / relative_path,
                dirs_exist_ok=True,
            )
    print(f"Сохранено в {output}: {', '.join(selected)}", flush=True)


def main() -> None:
    """Запустить исследование в проекте или во временной папке с выгрузкой."""
    args, selected = parse_arguments()

    # Обычный локальный запуск сохраняет результаты прямо в проекте.
    if (
        args.output_dir is None
        and args.input == ROOT / "data/raw/Steel_industry_data.csv"
        and args.save == "all"
    ):
        run_notebooks(ROOT)
        return
    output = (args.output_dir or ROOT).resolve()
    prepare_output_directory(output)
    with tempfile.TemporaryDirectory(prefix="steel-pipeline-") as temporary:
        workspace = Path(temporary)
        prepare_workspace(workspace, args.input)
        run_notebooks(workspace)
        save_results(workspace, output, selected)


if __name__ == "__main__":
    main()
