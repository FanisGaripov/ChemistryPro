# ChemistryPRO - веб-приложение для изучения школьного курса Химии

[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.1%2B-green)](https://flask.palletsprojects.com/)
[![Render](https://img.shields.io/badge/deployed%20on-Render-purple)](https://render.com/)
[![License](https://img.shields.io/badge/license-Apache%202.0-red)](LICENSE)

## 📋 Содержание
- [О проекте](#о-проекте)
- [Функциональность](#функциональность)
- [Технологии](#-технологии)
- [Начало работы](#начало-работы)
- [Запуск](#запуск)
- [Структура проекта](#структура-проекта)
- [API Endpoints](#-api-endpoints)
- [Автор и благодарности](#-автор)


## О проекте

Проект предлагает пользователям различные функции для взаимодействия с данными о химических элементах. Сайт задеплоен на render.com: https://chemistrypro.onrender.com/


## Функциональность

- **Цепочки превращений:** Создавайте цепочки превращений химических реакций
- **Органические реакции:** Решение органических реакций
- **Уравнивание реакций:** Уравнивайте химические реакции разной сложности
- **Дописывание реакций:** Функция дописывания продуктов реакции
- **Молярные массы:** Калькулятор молярных масс веществ и химических реакций
- **Электронная конфигурация:** Справочник электронных конфигураций химических элементов
- **Структура органических веществ:** Узнаем структуру органических веществ при помощи его названия / графического ввода
- **ChemistryPRO AI Assistant:** Интеграция с ChatGPT-4
- **Просмотр 3D-молекул:** Объемное представление органических веществ
- **Задания ОГЭ/ЕГЭ:** Создавайте цепочки превращений химических реакций с помощью нашего онлайн-инструмента
- **Интерактивные таблицы** Таблица Менделеева, Таблица Растворимостей, Таблица Кислот


## 🛠 Технологии

- **Backend:** Flask, SQLAlchemy, Gunicorn
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap
- **База данных:** SQLite (dev), PostgreSQL (prod)
- **Деплой:** Render.com
- **Линтеры:** Flake8, Black


## Начало работы

### Скачайте архив проекта или клонируйте репозиторий:
```
git clone https://github.com/FanisGaripov/ChemistryPro.git
```
### Перейдите в папку проекта:
```
cd ChemistryPRO
```
### Как создать виртуальное окружение:
Windows/Linux/macOS:

```
python3 -m venv venv
```

Linux/macOS:

```
source venv/bin/activate
```

Windows:

```
venv\Scripts\activate
```


### Установка нужных библиотек для прода:
```
pip install -r requirements/prod.txt
```

### Установка нужных библиотек для dev(разработки):
```
pip install -r requirements/dev.txt
```

### Создайте .env-файл или переименуйте template.env(шаблон) в .env
```
cp template.env .env
```

### Отредактируйте .env-файл:
```
YANDEX_TOKEN='свой токен от яндекс диска'
DATABASE='база данных'
...
```

### Чтобы запустить проект в dev-режиме, измените пункт debug в .env файле
### С состояния False
```
DEBUG=False
```
### В True
```
DEBUG=True
```

## Запуск:
```
cd src
python3 server.py
```

Таким образом сервер будет запущен и доступен по ссылке: http://127.0.0.1:5000


## Структура проекта:
```
ChemistryPro/
├── .github/workflows       # CI/CD
├── requirements            # Зависимости
│   ├── dev.txt                    # Для разработки
│   ├── prod.txt                   # Для production
│   └── lint.txt                   # Для линтера
├── src                     # Исходный код
│   ├── api                        # blueprint API
│   ├── instance                   # SQLite база данных
│   ├── static/                    # Статические файлы, такие как CSS и изображения
│   │   ├── /upload
│   │   └── fon.jpg...
│   ├── templates/                 # Шаблоны HTML
│   │   ├── includes/              # Части базового шаблона
│   │   ├── base.html              # Базовый шаблон
│   │   └── main.html...           # Главная страница
│   ├── База заданий ЕГЭ
│   ├── База заданий ОГЭ
│   ├── __init__.py
│   ├── mod.py                     # Модели базы данных
│   ├── qualitative_reactions.py   # Проверка на качественные реакции
│   ├── server.py                  # Серверная логика
│   ├── utils.py                   # Химические функции
├── .flake8                 # Конфигурация линтера flake8
├── .gitignore              # Стандартный gitignore python
├── LICENSE                 # Apache License 2.0
├── README.txt              # Старый README
├── README.md               # Этот файл
├── pyproject.toml          # Конфигурация black
└── template.env            # Шаблон .env файла

```

## 🔌 API Endpoints

| Метод | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/get_reaction_chain/<q>` | Цепочка превращений |
| GET | `/api/organic_reactions/<q>` | Органические реакции |
| GET | `/api/balancing_reactions/<q>` | Уравнивание реакций |
| GET | `/api/molyar_mass/<q>` | Посчитать молярную массу |
| GET | `/api/complete_reactions/<q>` | Дописывание реакций |
| GET | `/api/electronic_confuguration/<q>` | Электронная конфигурация элемента |
| GET | `/api/chatgpt/<q>` | ChatGPT (gpt-4) |

Пример запроса:
```bash
curl https://chemistrypro.onrender.com/api/get_reaction_chain/Al=Al2O3
```

Ответ:
```bash
{
  "answer": "Как из Al → Al2O3: \n2Al + Cr2O3 = Al2O3 + 2Cr \nFe2O3 + 2Al = Al2O3 + 2Fe \n3Li2O + 2Al `overset(t)(=)` 6Li + Al2O3 \n3V2O5 + 10Al = 5Al2O3 + 6V \n3CuO + 2Al = Al2O3 + 3Cu \n2Al + WO3 = Al2O3 + W \n2Al + 3PbO = 3Pb + Al2O3 \n4Al + 3O2 = 2Al2O3 \n3MnO + 2Al = 3Mn + Al2O3"
}
```


## ✍️ Автор

- **Фанис Гарипов** - *Разработчик* - [GitHub](https://github.com/FanisGaripov)

## 🙏 Благодарности

- Всем, кто тестировал приложение и давал обратную связь
