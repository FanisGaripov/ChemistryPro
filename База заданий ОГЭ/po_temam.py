import re
import json

def clean_filename(text):
    cleaned = ''
    if text is not None:
        cleaned = re.sub(r'[^\w\s-]', '', text.strip())
    else:
        text = 'ТЕМА_НЕОПРЕДЕЛЕНА'
        cleaned = re.sub(r'[^\w\s-]', '', text.strip())
    cleaned = re.sub(r'[-\s]+', '_', cleaned)
    return cleaned[:50]  # Ограничиваем длину имени файла


with open('fipi_tasks.json', 'r', encoding='utf-8') as f:
    tasks = json.load(f)
tasks_by_type = {}
for task in tasks:
    task_type = task['topic']
    if task_type not in tasks_by_type:
        tasks_by_type[task_type] = []
    tasks_by_type[task_type].append(task)

for task_type, type_tasks in tasks_by_type.items():
    safe_name = clean_filename(task_type)
    filename = f'tasks_type_{safe_name}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(type_tasks, f, ensure_ascii=False, indent=2)

print(f"Задания отсортированы по {len(tasks_by_type)} типам")