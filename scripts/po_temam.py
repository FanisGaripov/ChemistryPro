import json
import os
import re


def clean_filename(text):
    """Очищает название темы для использования в имени файла (макс 50 символов)"""
    if text is None:
        text = "ТЕМА_НЕОПРЕДЕЛЕНА"
    cleaned = re.sub(r"[^\w\s-]", "", text.strip())
    cleaned = re.sub(r"[-\s]+", "_", cleaned)
    return cleaned[:50]


def merge_tasks(existing, new):
    """Объединяет задания из существующего и нового списка, избегая дубликатов"""
    existing_ids = {task["id"] for task in existing}
    for task in new:
        if task["id"] not in existing_ids:
            existing.append(task)
    return existing


# Загрузка данных
with open("fipi_tasks.json", "r", encoding="utf-8") as f:
    tasks = json.load(f)

# Группировка по темам
tasks_by_type = {}
for task in tasks:
    task_type = task.get("topic", "ТЕМА_НЕОПРЕДЕЛЕНА")
    if task_type not in tasks_by_type:
        tasks_by_type[task_type] = []
    tasks_by_type[task_type].append(task)

# Сохранение в файлы
saved_count = 0
for task_type, type_tasks in tasks_by_type.items():
    safe_name = clean_filename(task_type)
    filename = f"tasks_type_{safe_name}.json"

    # Если файл существует - загружаем и объединяем данные
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                existing_tasks = json.load(f)
            merged_tasks = merge_tasks(existing_tasks, type_tasks)
        except:
            merged_tasks = type_tasks
    else:
        merged_tasks = type_tasks

    # Сохраняем объединенные данные
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(merged_tasks, f, ensure_ascii=False, indent=2)
        saved_count += 1

# Статистика
tasks_with_images = sum(1 for task in tasks if task.get("image"))
print(f"Всего заданий: {len(tasks)}")
print(f"Из них с картинками: {tasks_with_images}")
print(f"Сохранено файлов: {saved_count}")
print(f"Уникальных тем: {len(tasks_by_type)}")
