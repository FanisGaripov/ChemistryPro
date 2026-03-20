import json
import os
import random
import re
from datetime import datetime
from string import ascii_letters, digits

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    stream_with_context,
    url_for,
)
import flask_login
import g4f
import requests

from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from deep_translator import MyMemoryTranslator
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from mod import User, UserGameState, db
from api.api import api
from qualitative_reactions import qualitative_reactions_notorganic
from utils import (
    electronic_configuration,
    get_chemical_equation_solution,
    get_reaction_chain,
    molecular_mass,
    organic_reactions,
    uravnivanie,
)

# импортируем все библиотеки

app = Flask(__name__)
load_dotenv()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///products.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/upload"
app.secret_key = "supersecretkey"
app.register_blueprint(api, url_prefix="/api")
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
db.init_app(app)


def download_avatar_from_yandex_disk(filename):
    token = os.getenv("YANDEX_TOKEN")
    headers = {"Authorization": f"OAuth {token}"}

    # Получение ссылки для загрузки
    download_url = f"https://cloud-api.yandex.net/v1/disk/resources/download?path=users_avatars/{filename}"
    response = requests.get(download_url, headers=headers)
    if filename != "chat_history.json":
        if response.status_code == 200:
            download_link = response.json().get("href")

            # Проверяем, получена ли ссылка на загрузку
            if not download_link:
                print(f"No download link received for {filename}.")
                return False

            # Загрузка файла
            avatar_response = requests.get(download_link)

            if avatar_response.status_code == 200:
                with open(os.path.join("static/upload", filename), "wb") as f:
                    f.write(avatar_response.content)
                return True
            else:
                print(
                    f"Failed to download the file. Status code: {avatar_response.status_code}"
                )
                print(f"Response content: {avatar_response.content}")
        else:
            print(
                f"Failed to get download URL. Status code: {response.status_code}"
            )
            print(f"Response content: {response.content}")
    elif filename == "chat_history.json":
        if response.status_code == 200:
            download_link = response.json().get("href")
            if not download_link:
                print(f"No download link received for {filename}.")
                return False

            avatar_response = requests.get(download_link)

            if avatar_response.status_code == 200:
                with open(os.path.join("", filename), "wb") as f:
                    f.write(avatar_response.content)
                return True
            else:
                print(
                    f"Failed to download chat file. Status code: {avatar_response.status_code}"
                )
                print(f"Response content: {avatar_response.content}")
        else:
            print(
                f"Failed to get download URL. Status code: {response.status_code}"
            )
            print(f"Response content: {response.content}")

    return False


def check_and_download_avatars():
    users = User.query.all()
    for user in users:
        if user.avatar:
            avatar_path = os.path.join("static/upload", user.avatar)
            if not os.path.exists(avatar_path):
                print(
                    f"Avatar for user {user.username} not found, downloading from Yandex Disk..."
                )
                if download_avatar_from_yandex_disk(user.avatar):
                    print(
                        f"Avatar for user {user.username} downloaded successfully."
                    )
                else:
                    print(
                        f"Failed to download avatar for user {user.username}."
                    )
        else:
            print(f"User {user.username} has no avatar defined.")


def load_tasks_from_files(number):
    catalog = {}
    if number == 1:
        tasks_dir = "База заданий ОГЭ"
    else:
        tasks_dir = "База заданий ЕГЭ"

    for filename in os.listdir(tasks_dir):
        if filename.startswith("tasks_type_") and filename.endswith(".json"):
            theme = filename.replace("tasks_type_", "").replace(".json", "")
            try:
                with open(
                    os.path.join(tasks_dir, filename), "r", encoding="utf-8"
                ) as f:
                    tasks = json.load(f)
                    catalog[theme] = tasks
            except Exception as e:
                print(f"Ошибка загрузки файла {filename}: {e}")

    return catalog


oge_catalog = load_tasks_from_files(1)
ege_catalog = load_tasks_from_files(2)
PRETTY_CATEGORY_NAMES_OGE = {
    # Раздел 1. Основные понятия химии
    "11_Чистые_вещества_и_смеси_Способы_разделения_смес": "Чистые вещества и смеси. Способы разделения смесей",
    "12_Атомы_и_молекулы_Химические_элементы_Символы_хи": "Атомы и молекулы. Химические элементы. Символы химических элементов",
    "13_Химическая_формула_Валентность_атомов_химически": "Химическая формула. Валентность атомов химических элементов",
    "14_Закон_постоянства_состава_веществ_Относительная": "Закон постоянства состава веществ. Относительная атомная и молекулярная массы",
    "16_Физические_и_химические_явления_Химическая_реак": "Физические и химические явления. Химическая реакция",
    # Раздел 2. Периодический закон и строение атома
    "21_Периодический_закон_Периодическая_система_химич": "Периодический закон. Периодическая система химических элементов",
    "22_Строение_атомов_Состав_атомных_ядер_Изотопы_Эле": "Строение атомов. Состав атомных ядер. Изотопы. Электроны",
    "23_Закономерности_в_изменении_свойств_химических_э": "Закономерности в изменении свойств химических элементов",
    # Раздел 3. Химическая связь и строение вещества
    "31_Химическая_связь_Ковалентная_полярная_и_неполяр": "Химическая связь. Ковалентная (полярная и неполярная)",
    "32_Типы_кристаллических_решёток_атомная_ионная_мет": "Типы кристаллических решёток (атомная, ионная, металлическая)",
    # Раздел 4. Неорганическая химия
    "410_Получение_собирание_распознавание_водорода_кис": "Получение, собирание и распознавание водорода, кислорода",
    "412_Генетическая_связь_между_классами_неорганическ": "Генетическая связь между классами неорганических соединений",
    "41_Классификация_и_номенклатура_неорганических_сое": "Классификация и номенклатура неорганических соединений",
    "42_Физические_и_химические_свойства_простых_вещест": "Физические и химические свойства простых веществ",
    "44_Физические_и_химические_свойства_водородных_сое": "Физические и химические свойства водородных соединений",
    # Раздел 5. Химические реакции
    "51_Классификация_химических_реакций_по_различным_п": "Классификация химических реакций по различным признакам",
    "53_Окислительновосстановительные_реакции_Окислител": "Окислительно-восстановительные реакции. Окислитель и восстановитель",
    "54_Теория_электролитической_диссоциации_Катионы_ан": "Теория электролитической диссоциации. Катионы и анионы",
    "55_Реакции_ионного_обмена_Условия_протекания_реакц": "Реакции ионного обмена. Условия протекания реакций",
    # Раздел 6. Химия и жизнь
    "61_Вещества_и_материалы_в_повседневной_жизни_челов": "Вещества и материалы в повседневной жизни человека",
    "62_Химическое_загрязнение_окружающей_среды_кислотн": "Химическое загрязнение окружающей среды. Кислотные дожди",
    # Раздел 7. Расчетные задачи
    "71_Расчёты_по_формулам_химических_соединений72_Рас": "Расчёты по формулам химических соединений",
    "71_Расчёты_по_формулам_химических_соединений73_Рас": "Расчёты по уравнениям химических реакций",
    "72_Расчёты_массымассовой_доли_растворённого_вещест": "Расчёты массы и массовой доли растворённого вещества",
}
PRETTY_CATEGORY_NAMES_EGE = {
    # Раздел 1. Теоретические основы химии
    "11_Строение_вещества_Современная_модель_строения_а": "Строение вещества. Современная модель строения атома",
    "12_Периодическая_система_химических_элементов_ДИ_М": "Периодическая система химических элементов Д.И. Менделеева",
    "13_Валентность_Электроотрицательность_Степень_окис": "Валентность. Электроотрицательность. Степень окисления",
    "14_Виды_химической_связи_ковалентная_ионная_металл": "Виды химической связи (ковалентная, ионная, металлическая)",
    "15_Химическая_реакция_Классификация_химических_реа": "Химическая реакция. Классификация химических реакций",
    "16_Скорость_реакции_её_зависимость_от_различных_фа": "Скорость реакции и её зависимость от различных факторов",
    "18_Обратимые_реакции_Химическое_равновесие_Факторы": "Обратимые реакции. Химическое равновесие. Факторы смещения равновесия",
    "19_Электролитическая_диссоциация_Сильные_и_слабые_": "Электролитическая диссоциация. Сильные и слабые электролиты",
    "110_Гидролиз_солей_Ионное_произведение_воды_Водоро": "Гидролиз солей. Ионное произведение воды. Водородный показатель",
    "111_Способы_выражения_концентрации_растворов_массо": "Способы выражения концентрации растворов (массовая доля, молярность)",
    "112_Окислительно_восстановительные_реакции_Поведен": "Окислительно-восстановительные реакции. Поведение веществ в ОВР",
    "113_Электролиз_растворов_и_расплавов_солей": "Электролиз растворов и расплавов солей",
    # Раздел 2. Неорганическая химия
    "21_Классификация_неорганических_соединений_Номенкл": "Классификация неорганических соединений. Номенклатура",
    "22_Химические_свойства_важнейших_металлов_натрий_к": "Химические свойства важнейших металлов (натрий, калий, магний, кальций, алюминий, цинк, хром, железо, медь, серебро)",
    "24_Генетическая_связь_неорганических_веществ_прина": "Генетическая связь неорганических веществ. Принадлежность к классам",
    "25_Идентификация_неорганических_соединений_Качеств": "Идентификация неорганических соединений. Качественные реакции",
    # Раздел 3. Органическая химия
    "31_Основные_положения_теории_химического_строения_": "Основные положения теории химического строения А.М. Бутлерова",
    "33_Представление_о_классификации_органических_веще": "Классификация органических веществ. Основные классы соединений",
    "34_Свободнорадикальный_и_ионный_механизмы_реакции_": "Механизмы химических реакций (свободнорадикальный, ионный)",
    "35_Алканы_Химические_свойства_алканов_галогенирова": "Алканы. Химические свойства (галогенирование, горение, крекинг)",
    "310_Спирты_Предельные_одноатомные_спирты_Химически": "Спирты. Предельные одноатомные спирты. Химические свойства",
    "312_Альдегиды_Химические_свойства_предельных_альде": "Альдегиды. Химические свойства предельных альдегидов",
    "314_Сложные_эфиры_и_жиры_Способы_получения_сложных": "Сложные эфиры и жиры. Способы получения. Химические свойства",
    "315_Химические_свойства_глюкозы_реакции_с_участием": "Углеводы. Глюкоза. Химические свойства (реакции с участием альдегидной и гидроксильных групп)",
    "316_Амины_Амины_как_органические_основания_реакции": "Амины. Амины как органические основания. Реакции с кислотами",
    "317_Аминокислоты_и_белки_Аминокислоты_как_амфотерн": "Аминокислоты и белки. Аминокислоты как амфотерные соединения",
    "318_Строение_и_структура_полимеров_Зависимость_сво": "Полимеры. Строение и структура. Зависимость свойств от строения",
    "320_Генетическая_связь_между_классами_органических": "Генетическая связь между классами органических соединений",
    # Раздел 4. Расчетные задачи
    "51_Расчёты_массы_вещества_или_объёма_газов_по_изве": "Расчёты массы вещества или объёма газов по известному количеству вещества",
    "52_Расчёты_теплового_эффекта_реакции": "Расчёты теплового эффекта реакции",
    "53_Расчёты_объёмных_отношений_газов_при_химических": "Расчёты объёмных отношений газов при химических реакциях",
    "54_Расчёты_массы_объёма_количества_вещества_продук": "Расчёты массы, объёма, количества вещества продукта реакции по исходному веществу",
    "55_Расчёты_массовой_или_объёмной_доли_выхода_проду": "Расчёты массовой или объёмной доли выхода продукта реакции",
    "57_Расчёты_с_использованием_понятий_массовая_доля_": "Расчёты с использованием понятий массовая доля, молярная концентрация",
    "58_Нахождение_молекулярной_формулы_органического_в": "Нахождение молекулярной формулы органического вещества",
}


@app.context_processor
def inject_now():
    return {"now": datetime.now()}


@app.route("/change_language/ru", methods=["GET", "POST"])
def language_ru():
    if "page" not in session:
        session["page"] = "/"
        session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    session["language"] = "Ru"
    session.modified = True
    return redirect(session["page"])


@app.route("/change_language/tat", methods=["GET", "POST"])
def language_tat():
    if "page" not in session:
        session["page"] = "/"
        session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    session["language"] = "Tat"
    session.modified = True
    return redirect(session["page"])


@app.route("/oge", methods=["GET", "POST"])
def OGE_catalog():
    if "page" not in session:
        session["page"] = "/oge"
        session.modified = True
    session["page"] = "/oge"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template(
            "oge_catalog.html", catalog=oge_catalog, user=user
        )
    else:
        return render_template(
            "oge_catalog_tat.html", catalog=oge_catalog, user=user
        )


@app.route("/oge/<category>")
def OGE_zadaniya(category):
    if "page" not in session:
        session["page"] = f"/oge/{category}"
        session.modified = True
    session["page"] = f"/oge/{category}"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    tasks = oge_catalog.get(category, [])
    pretty_category = PRETTY_CATEGORY_NAMES_OGE.get(
        category, category.replace("_", " ")
    )
    if session["language"] == "Ru":
        return render_template(
            "OGE.html",
            category=category,
            tasks=tasks,
            user=user,
            pretty_category=pretty_category,
        )
    else:
        return render_template(
            "OGE_tat.html",
            category=category,
            tasks=tasks,
            user=user,
            pretty_category=pretty_category,
        )


@app.route("/ege", methods=["GET", "POST"])
def EGE_catalog():
    if "page" not in session:
        session["page"] = "/ege"
        session.modified = True
    session["page"] = "/ege"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template(
            "ege_catalog.html", catalog=ege_catalog, user=user
        )
    else:
        return render_template(
            "ege_catalog_tat.html", catalog=ege_catalog, user=user
        )


@app.route("/ege/<category>")
def EGE_zadaniya(category):
    if "page" not in session:
        session["page"] = f"/ege/{category}"
        session.modified = True
    session["page"] = f"/ege/{category}"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    tasks = ege_catalog.get(category, [])
    pretty_category = PRETTY_CATEGORY_NAMES_EGE.get(
        category, category.replace("_", " ")
    )
    if session["language"] == "Ru":
        return render_template(
            "EGE.html",
            category=category,
            tasks=tasks,
            user=user,
            pretty_category=pretty_category,
        )
    else:
        return render_template(
            "EGE_tat.html",
            category=category,
            tasks=tasks,
            user=user,
            pretty_category=pretty_category,
        )


def generate_graphical_representation(configurations):
    # графическое представление электронной конфигурации
    representation = []
    grouped_representation = {}

    for config in configurations:
        subshell, count = config.split("^")
        count = int(count)

        if subshell[0] not in grouped_representation:
            grouped_representation[subshell[0]] = []

        cells = []

        if subshell.endswith("s"):
            for _ in range(1):
                if count > 0:
                    cells.append("[↑]")
                    count -= 1
                if count > 0:
                    cells[0] += "[↓]"
                    count -= 1
                else:
                    cells.append("[ ]")  # Пустая ячейка

        elif subshell.endswith("p"):
            # 3 p-орбитали
            for i in range(3):
                if count > 0:
                    cells.append("[↑]")
                    count -= 1
                else:
                    cells.append("[ ]")  # Пустая ячейка

            for i in range(3):
                if count > 0:
                    cells[i] += "[↓]"
                    count -= 1

        elif subshell.endswith("d"):
            # 5 d-орбиталей
            for i in range(5):
                if count > 0:
                    cells.append("[↑]")
                    count -= 1
                else:
                    cells.append("[ ]")  # Пустая ячейка

            for i in range(5):
                if count > 0:
                    cells[i] += "[↓]"
                    count -= 1

        elif subshell.endswith("f"):
            # 7 f-орбиталей
            for i in range(7):
                if count > 0:
                    cells.append("[↑]")
                    count -= 1
                else:
                    cells.append("[ ]")  # Пустая ячейка

            for i in range(7):
                if count > 0:
                    cells[i] += "[↓]"
                    count -= 1

        grouped_representation[subshell[0]].append(
            f"{subshell}: " + " ".join(cells)
        )

    # Сборка финального представления
    for level in sorted(grouped_representation.keys()):
        representation.extend(grouped_representation[level])

    return "\n".join(representation)


@app.route("/electronic_configuration", methods=["GET", "POST"])
def electronic_configuration_page():
    if "page" not in session:
        session["page"] = "/electronic_configuration"
        session.modified = True
    session["page"] = "/electronic_configuration"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # функция, которая отображает страницу электронной конфигурации, предыдущая функция отвечает за обработку ответа
    element = ""
    config = ""
    atomic_num = ""
    user = flask_login.current_user
    configuration = ""
    configuration1 = ""
    graphic_representation = ""
    atomic = ""
    if request.method == "POST":
        element = request.form.get("element", False)
        try:
            configuration, configuration1, graphic_representation, atomic = (
                electronic_configuration(element)
            )
            config = get_electron_config(int(atomic))
        except Exception as e:
            configuration1, configuration, graphic_representation, atomic = (
                "",
                "",
                "",
                "",
            )
    if session["language"] == "Ru":
        return render_template(
            "electronic_configuration.html",
            configuration=configuration,
            configuration1=configuration1,
            graphic_representation=graphic_representation,
            atomic=atomic,
            user=user,
            element=element,
            config=config,
            atomic_number=atomic,
            current_element=element,
        )
    else:
        render_template(
            "electronic_configuration_tat.html",
            configuration=configuration,
            configuration1=configuration1,
            graphic_representation=graphic_representation,
            atomic=atomic,
            user=user,
            element=element,
            config=config,
            atomic_number=atomic,
            current_element=element,
        )


@app.route("/", methods=["GET", "POST"])
def main():
    if "page" not in session:
        session["page"] = "/"
        session.modified = True
    session["page"] = "/"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # функция, которая возвращает главную страницу сайта( main.html )
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template("main.html", user=user)
    else:
        return render_template("main_tat.html", user=user)


@app.route("/uravnivanie", methods=["GET", "POST"])
def osnova():
    if "page" not in session:
        session["page"] = "/uravnivanie"
        session.modified = True
    session["page"] = "/uravnivanie"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # функция которая возвращает уравнивание хим.реакций( index.html )
    user = flask_login.current_user
    resultat2 = ""
    if request.method == "POST":
        chemical_formula = request.form["chemical_formula"]
        try:
            resultat2 = f"{chemical_formula}: {uravnivanie(chemical_formula)}"
        except:
            redirect("/")
    if session["language"] == "Ru":
        return render_template("index.html", resultat2=resultat2, user=user)
    else:
        return render_template(
            "index_tat.html", resultat2=resultat2, user=user
        )


@app.route("/molyarnaya_massa", methods=["GET", "POST"])
def molyar_massa():
    if "page" not in session:
        session["page"] = "/molyarnaya_massa"
        session.modified = True
    session["page"] = "/molyarnaya_massa"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # метод для вычисления молярной массы и отображения ее на сайте
    user = flask_login.current_user
    global resultat, dlyproverki
    resultat = ""
    otdelno = []
    formatspisok = ""
    dlyproverki = 0
    if request.method == "POST":
        chemical_formula = request.form["element"]
        try:
            dlyproverki, element_details = molecular_mass(chemical_formula)
            resultat = (
                f"Молярная масса {chemical_formula}: {dlyproverki} г/моль"
            )
            for element, mass, count, total_mass in element_details:
                otdelno.append(
                    f"{count} x {element} ({round(mass, 2)} г/моль): {round(total_mass, 2)} г/моль, что составляет {round((round(total_mass, 2) / dlyproverki) * 100, 2)}%"
                )
        except Exception as e:
            otdelno.append(
                f"{e}: такого вещества или соединения не существует"
            )
    if session["language"] == "Ru":
        return render_template(
            "molyarnaya_massa.html",
            resultat=resultat,
            dlyproverki=dlyproverki,
            user=user,
            otdelno=otdelno,
        )
    else:
        return render_template(
            "molyarnaya_massa_tat.html",
            resultat=resultat,
            dlyproverki=dlyproverki,
            user=user,
            otdelno=otdelno,
        )


@app.route("/complete_reaction", methods=["GET", "POST"])
def complete_reaction_page():
    if "page" not in session:
        session["page"] = "/complete_reaction"
        session.modified = True
    session["page"] = "/complete_reaction"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # страница, отвечающая за вывод завершенных реакций предыдущим методом
    react1 = ""
    check_qualitative_reaction_notorganic = ""
    user = flask_login.current_user
    reaction = ""
    if request.method == "POST":
        reaction = request.form.get("chemical_formula", False)
        react1 = get_chemical_equation_solution(reaction)
        if "(g)" in react1:
            react1 = react1.replace("(g)", "")
        if "(s)" in react1:
            react1 = react1.replace("(s)", "")
        if "(aq)" in react1:
            react1 = react1.replace("(aq)", "")
        if "(l)" in react1:
            react1 = react1.replace("(l)", "")
        if qualitative_reactions_notorganic(reaction):
            check_qualitative_reaction_notorganic = (
                qualitative_reactions_notorganic(reaction)
            )

    if session["language"] == "Ru":
        return render_template(
            "complete_reaction.html",
            get_chemical_equation_solution=get_chemical_equation_solution,
            react1=react1,
            user=user,
            reaction=reaction,
            check_qualitative_reaction_notorganic=check_qualitative_reaction_notorganic,
        )
    else:
        return render_template(
            "complete_reaction_tat.html",
            get_chemical_equation_solution=get_chemical_equation_solution,
            react1=react1,
            user=user,
            reaction=reaction,
            check_qualitative_reaction_notorganic=check_qualitative_reaction_notorganic,
        )


@app.route("/get_reaction_chain", methods=["GET", "POST"])
def get_reaction_chain_page():
    if "page" not in session:
        session["page"] = "/get_reaction_chain"
        session.modified = True
    session["page"] = "/get_reaction_chain"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # страница, которая выводит цепочку превращений, т.е прошлую функцию
    user = flask_login.current_user
    react2 = ""
    reaction = ""
    if request.method == "POST":
        reaction = request.form.get("chemical_formula", False)
        react2 = get_reaction_chain(reaction)

    if session["language"] == "Ru":
        return render_template(
            "get_reaction_chain.html",
            get_reaction_chain=get_reaction_chain,
            user=user,
            reaction=reaction,
            react2=react2,
        )
    else:
        return render_template(
            "get_reaction_chain_tat.html",
            get_reaction_chain=get_reaction_chain,
            user=user,
            reaction=reaction,
            react2=react2,
        )


@app.route("/organic_reactions", methods=["GET", "POST"])
def organic():
    if "page" not in session:
        session["page"] = "/organic_reactions"
        session.modified = True
    session["page"] = "/organic_reactions"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    zapros = ""
    if request.method == "POST":
        zapros = request.form.get("chemical_formula", False)
        image_tags, dec_ans2 = organic_reactions(zapros)
        if session["language"] == "Ru":
            return render_template(
                "organic_reactions.html",
                user=user,
                image_tags=image_tags,
                zapros=zapros.capitalize(),
                dec_ans2=dec_ans2,
            )
        else:
            return render_template(
                "organic_reactions_tat.html",
                user=user,
                image_tags=image_tags,
                zapros=zapros.capitalize(),
                dec_ans2=dec_ans2,
            )
    if session["language"] == "Ru":
        return render_template(
            "organic_reactions.html", user=user, image_tags=None
        )
    else:
        return render_template(
            "organic_reactions_tat.html", user=user, image_tags=None
        )


@app.route("/send_coordinates", methods=["POST"])
def send_coordinates():
    tabinf = ""
    data = request.json
    coordinates = data.get("coordinates", [])
    responses = []
    instr = ""

    for coord in coordinates:
        X_coord = coord["x"]
        Y_coord = coord["y"]
        element = coord["element"]
        if element == "C":
            instr = "01"
        elif element == "O":
            instr = "02"
        elif element == "N":
            instr = "03"
        elif element == "S":
            instr = "04"
        elif element == "F":
            instr = "05"
        elif element == "Cl":
            instr = "06"
        elif element == "Br":
            instr = "07"
        elif element == "I":
            instr = "08"
        elif element == "Na":
            instr = "09"
        elif element == "K":
            instr = "10"

        if tabinf == "":
            url = f"http://acetyl.ru/process/graf.php?instr={instr}&tx={X_coord}&ty={Y_coord}&tz=00&tabinf=&test=0&ww=985"
        else:
            url = f"http://acetyl.ru/process/graf.php?instr={instr}&tx={X_coord}&ty={Y_coord}&tz=00&tabinf={tabinf}&test=0&ww=985"

        response = requests.get(url)
        if response.status_code == 200:
            answer = response.text
            parsed_data = json.loads(answer)
            tabinf = parsed_data["tabinf"]
            substance = parsed_data["res"]
            responses.append(substance[0])
            photo_url = f"http://acetyl.ru/s/{substance[1]}.png"
            session["photo_url"] = photo_url
            session["substance_name"] = substance[0]

    return jsonify(responses)


@app.route("/organic_substance", methods=["GET", "POST"])
def organic_substance():
    if "page" not in session:
        session["page"] = "/organic_substance"
        session.modified = True
    session["page"] = "/organic_substance"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    k = 0
    image_tags = []
    user = flask_login.current_user
    photo_url = session.get("photo_url", None)
    substance_name = session.get("substance_name", None)
    substance_name_new = ""
    if (
        substance_name is not None
        and "<br>Чтобы продолжить цепь, кликните по любой <em>свободной</em> клетке рядом"
        in substance_name
    ):
        substance_name = substance_name[0:5]
    image_container = ""
    if photo_url is not None and substance_name is not None:
        url = "http://acetyl.ru/process/recv.php"
        if "<br>" in substance_name:
            substance_name_new = substance_name.split("<br>")
            substance_name_new = substance_name_new[0]
        else:
            substance_name_new = substance_name

        # Параметры запроса
        params = {
            "search": substance_name_new,
            "sizesd": 1,
            "colsd": 0,
            "test": 0,
            "butt": 4,
        }

        # Отправка GET-запроса
        response = requests.get(url, params=params)

        # Проверка статуса ответа
        if response.status_code == 200:
            answer = response.text
            parsed_data = json.loads(answer)
            soup = BeautifulSoup(str(parsed_data), "html.parser")
            images = soup.find_all("img")
            for img in images:
                src = img["src"]
                title = img.get("title", "")
                if not src.startswith("http"):
                    src = f"http://acetyl.ru{src}"
                if (
                    src[-4::] != ".gif"
                    and src[-12::] != "wikiicon.png"
                    and src[-17::] != "starthelpicon.png"
                ):
                    k += 1
                    image_tags.append(
                        f'{k})<img src="{src}" alt="{img.get("alt", "")}" title="{title}">'
                    )
                    if title is not None:
                        image_tags.append(title)
                elif k == 0:
                    image_tags.append("Картинок нет")

        else:
            image_tags.append(
                f"Ошибка при получении страницы: {response.status_code}"
            )

    if session["language"] == "Ru":
        return render_template(
            "organic_substance.html",
            user=user,
            photo_url=photo_url,
            substance_name=substance_name,
            image_tags=image_tags,
            substance_name_new=substance_name_new,
        )
    else:
        return render_template(
            "organic_substance_tat.html",
            user=user,
            photo_url=photo_url,
            substance_name=substance_name,
            image_tags=image_tags,
            substance_name_new=substance_name_new,
        )


@app.route("/select-organic-input", methods=["GET", "POST"])
def red_or_blue_tablet():
    if "page" not in session:
        session["page"] = "/select-organic-input"
        session.modified = True
    session["page"] = "/select-organic-input"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template("red_or_blue_tablet.html", user=user)
    else:
        return render_template("red_or_blue_tablet_tat.html", user=user)


@app.route("/aboutme", methods=["GET", "POST"])
def aboutme():
    if "page" not in session:
        session["page"] = "/aboutme"
        session.modified = True
    session["page"] = "/aboutme"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # обо мне
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template("about.html", user=user)
    else:
        return render_template("about_tat.html", user=user)


@app.route("/instruction", methods=["GET", "POST"])
def instruction():
    if "page" not in session:
        session["page"] = "/instruction"
        session.modified = True
    session["page"] = "/instruction"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # инструкция
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template("instruction.html", user=user)
    else:
        return render_template("instruction_tat.html", user=user)


@app.route("/documentation")
def documentation():
    if "page" not in session:
        session["page"] = "/documentation"
        session.modified = True
    session["page"] = "/documentation"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template("documentation.html", user=user)
    else:
        return render_template("documentation_tat.html", user=user)


def validate_for_molecules(name):
    allowed_chars = ascii_letters + digits + ",._- ="
    return all(c in allowed_chars for c in name)


@app.route("/get_molecule", methods=["GET", "POST"])
@app.route("/get_molecule/<name>", methods=["GET", "POST"])
def get_molecule_from_url(name=None, parameter=True):
    if "page" not in session:
        session["page"] = "/get_molecule"
        session.modified = True
    session["page"] = "/get_molecule"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    if name == None:
        parameter = False
        if request.method == "POST":
            name = request.form.get("name")
        else:
            return render_template(
                "get_molecule.html", formula=None, user=user
            )
    if validate_for_molecules(name):
        translation = name
    else:
        translation = MyMemoryTranslator(
            source="ru-RU", target="en-US"
        ).translate(name)
    translation = re.sub(r"[^\w\s=,._-]", "", translation)
    # translation = translation.replace(',', '_')
    if len(translation.split()) > 1:
        translation = "-".join(translation.split())
    pubchem_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{translation}/record/SDF?record_type=3d"
    response = requests.get(pubchem_url)
    if response.status_code == 200:
        formula = response.text
    else:
        formula = None
    if parameter == True:
        if session["language"] == "Ru":
            return render_template(
                "get_molecule_from_url.html",
                formula=formula,
                user=user,
                name=name,
            )
        else:
            return render_template(
                "get_molecule_from_url_tat.html",
                formula=formula,
                user=user,
                name=name,
            )
    else:
        if session["language"] == "Ru":
            return render_template(
                "get_molecule.html", formula=formula, user=user
            )
        else:
            return render_template(
                "get_molecule_tat.html", formula=formula, user=user
            )


@app.route("/chat-gpt", methods=["GET", "POST"])
def chatgpt():
    if "page" not in session:
        session["page"] = "/chat-gpt"
        session.modified = True
    session["page"] = "/chat-gpt"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    if "chatgpt_history" not in session:
        session["chatgpt_history"] = []
        session.modified = True
    if session["language"] == "Ru":
        return render_template(
            "chatgpt.html", user=user, chat_history=session["chatgpt_history"]
        )
    else:
        return render_template(
            "chatgpt_tat.html",
            user=user,
            chat_history=session["chatgpt_history"],
        )


@app.route("/stream")
def stream():
    question = request.args.get("question")
    # Обновляем историю чата
    session["chatgpt_history"].append({"sender": "user", "text": question})
    session.modified = True

    response = ask_chemistry_question(question)
    return Response(
        stream_with_context(response_stream(response)),
        content_type="text/event-stream",
    )


def response_stream(response):
    for chunk in response:
        if isinstance(chunk, str):
            yield f"data: {chunk}\n\n"

    yield "data: [DONE]\n\n"


def ask_chemistry_question(question):
    """Функция для отправки вопроса ИИ и получения ответа с потоковым выводом."""
    full_response = ""
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": question}],
            stream=True,
        )
        for chunk in response:
            if isinstance(chunk, str):
                full_response += chunk
                yield chunk

    except Exception as e:
        yield f"Произошла ошибка: {e}"


@app.route("/save-chat-history", methods=["POST"])
def save_chat_history():
    if request.method == "POST":
        data = request.get_json()
        session["chatgpt_history"] = data.get("history", [])
        session.modified = True
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})


@app.route("/clear", methods=["POST"])
def clear_chatgpt_history():
    session.pop("chatgpt_history", None)
    session.modified = True  # Убедитесь, что изменения зарегистрированы
    return redirect("/chat-gpt")


@app.route("/rastvory", methods=["GET", "POST"])
def rastvory():
    if "page" not in session:
        session["page"] = "/rastvory"
        session.modified = True
    session["page"] = "/rastvory"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # калькулятор растворимостей
    user = flask_login.current_user
    if request.method == "POST":
        # Получаем данные из формы
        mass_solution = request.form.get(
            "mass_solution", type=float
        )  # Масса раствора (г)
        mass_solute = request.form.get(
            "mass_solute", type=float
        )  # Масса растворенного вещества (г)
        mass_fraction = request.form.get(
            "mass_fraction", type=float
        )  # Массовая доля (в %)

        # Выполняем расчеты
        if mass_solution and mass_solute is not None:
            # Если известны масса раствора и масса вещества, рассчитываем массовую долю
            mass_fraction = (mass_solute / mass_solution) * 100

        elif mass_solution and mass_fraction is not None:
            # Если известны масса раствора и массовая доля, рассчитываем массу растворенного вещества
            mass_solute = (mass_fraction / 100) * mass_solution

        elif mass_solute and mass_fraction is not None:
            # Если известны масса вещества и массовая доля, рассчитываем массу раствора
            mass_solution = mass_solute / (mass_fraction / 100)

        if session["language"] == "Ru":
            return render_template(
                "rastvory.html",
                mass_solution=mass_solution,
                mass_solute=mass_solute,
                mass_fraction=mass_fraction,
                user=user,
            )
        else:
            return render_template(
                "rastvory_tat.html",
                mass_solution=mass_solution,
                mass_solute=mass_solute,
                mass_fraction=mass_fraction,
                user=user,
            )
    if session["language"] == "Ru":
        return render_template("rastvory.html", user=user)
    else:
        return render_template("rastvory_tat.html", user=user)


@app.route("/reaction-output-calculator", methods=["GET", "POST"])
def reaction_output_calculator():
    if "page" not in session:
        session["page"] = "/reaction-output-calculator"
        session.modified = True
    session["page"] = "/reaction-output-calculator"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    if request.method == "POST":
        actual_output = request.form.get("actual_output", type=float)
        theoretical_output = request.form.get("theoretical_output", type=float)
        percent = request.form.get("percent", type=float)
        if actual_output and theoretical_output is not None:
            percent = (actual_output / theoretical_output) * 100
        elif actual_output and percent is not None:
            theoretical_output = actual_output / (percent / 100)
        elif theoretical_output and percent is not None:
            actual_output = theoretical_output * (percent / 100)
        if session["language"] == "Ru":
            return render_template(
                "output_calculator.html",
                user=user,
                percent=percent,
                actual_output=actual_output,
                theoretical_output=theoretical_output,
            )
        else:
            return render_template(
                "output_calculator_tat.html",
                user=user,
                percent=percent,
                actual_output=actual_output,
                theoretical_output=theoretical_output,
            )
    if session["language"] == "Ru":
        return render_template("output_calculator.html", user=user)
    else:
        return render_template("output_calculator_tat.html", user=user)


chat_history_file = "../chat_history.json"


@app.route("/get_messages", methods=["GET"])
def get_messages():
    return jsonify(load_chat_history())


# Загрузка истории чата из файла
def load_chat_history():
    if os.path.exists(chat_history_file):
        with open(chat_history_file, "r") as f:
            return json.load(f)  # Загружаем данные из JSON
    return []


# Сохранение сообщения в файл
def save_message(username, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    polzovatel = User.query.filter_by(username=username).first()
    avatarka = polzovatel.avatar
    chat_entry = {
        "timestamp": timestamp,
        "avatar": avatarka,
        "username": username,
        "message": message,
    }

    # Загружаем текущую историю чата
    chat_history = load_chat_history()
    chat_history.append(chat_entry)

    # Сохраняем обновленную историю в JSON-файл
    with open(chat_history_file, "w") as f:
        json.dump(chat_history, f, indent=4)


# Удаление всех сообщений разом(доступно только администраторам)
def delete_all_messages():
    chat_history = load_chat_history()
    chat_history.clear()
    if chat_history != "":
        with open(chat_history_file, "w") as f:
            json.dump(chat_history, f, indent=4)


# Удаление сообщения
def delete_message(index):
    chat_history = load_chat_history()
    if 0 <= index < len(chat_history):
        del chat_history[index]
        with open(chat_history_file, "w") as f:
            json.dump(chat_history, f, indent=4)


chat = load_chat_history()  # Загружаем историю чата при старте


@app.route("/chat", methods=["GET", "POST"])
def chat_messages():
    if "page" not in session:
        session["page"] = "/chat"
        session.modified = True
    session["page"] = "/chat"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # чат
    global chat
    user = flask_login.current_user
    if user.is_authenticated:
        if request.method == "POST":
            if "message" in request.form:  # Добавление сообщения
                s = request.form["message"]
                save_message(user.username, s)  # Сохраняем сообщение в файл
            elif "delete" in request.form:  # Удаление сообщения
                index = int(request.form["delete"])
                if user.admin == 1 or chat[index]["username"] == user.username:
                    delete_message(index)  # Удаляем сообщение
            elif "delete_all_messages" in request.form:
                if user.admin == 1:
                    delete_all_messages()
            chat = (
                load_chat_history()
            )  # Обновляем чат после сохранения/удаления
            return redirect(
                url_for("chat_messages")
            )  # Перенаправляем на ту же страницу
        if session["language"] == "Ru":
            return render_template("chat.html", user=user, chat=chat)
        else:
            return render_template("chat_tat.html", user=user, chat=chat)
    else:
        return redirect(url_for("login"))


@app.route("/chat/saving")
def chat_saving():
    # Загрузка истории чата
    with open("../chat_history.json", "r", encoding="utf-8") as f:
        chat_history = json.load(f)
    if chat_history != "[]":
        file_path = "chat_history.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            for entry in chat_history:
                # Форматирование строки
                formatted_message = f"{entry['timestamp']} - {entry['username']}: {entry['message']}\n"
                f.write(formatted_message)
        return send_file(file_path, as_attachment=True)
    else:
        return "Чат пуст"


def scheduled_task():
    chat_file_path = "../chat_history.json"
    upload_to_yandex_disk(chat_file_path, os.path.basename(chat_file_path))


scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_task, "interval", hours=1)
scheduler.start()


@app.route("/download-db")
def download_db():
    # ф-ция уже не нужна, т.к база данных переехала на postgresql, но все равно оставлю для локальных тестов :)
    user = flask_login.current_user
    if user.is_authenticated and user.admin == 1:
        try:
            return send_from_directory(
                directory="instance",  # Папка, где хранится база данных
                path="products.db",  # Имя файла базы данных
                as_attachment=True,  # Это указывает, что файл должен быть скачан
            )
        except Exception as e:
            return str(e), 404
    else:
        bugcode = 6
        return render_template("bug.html", bugcode=bugcode, user=user)


@app.route("/tablica", methods=["GET", "POST"])
def tablica():
    if "page" not in session:
        session["page"] = "/tablica"
        session.modified = True
    session["page"] = "/tablica"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # таблица менделеева
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template("moretable.html", user=user)
    else:
        return render_template("moretable_tat.html", user=user)


@app.route("/tablica_old", methods=["GET", "POST"])
def tablica_old():
    if "page" not in session:
        session["page"] = "/tablica_old"
        session.modified = True
    session["page"] = "/tablica_old"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template("tablica_old.html", user=user)
    else:
        return render_template("tablica_old_tat.html", user=user)


@app.route("/sw.js")
def sw():
    return app.send_static_file("sw.js")


@app.route("/yandex_682e07bf768831de.html")
def ya():
    user = flask_login.current_user
    return render_template("yandex_682e07bf768831de.html", user=user)


@app.route("/googled5c4e477b332cb57.html")
def google():
    user = flask_login.current_user
    return render_template("googled5c4e477b332cb57.html", user=user)


@app.route("/ads.txt")
def ads():
    return app.send_static_file("ads.txt")


@app.route("/offline.html")
def offline():
    return app.send_static_file("offline.html")


@app.route("/tablica_rastvorimosti", methods=["GET", "POST"])
def tablica_rastvorimosti():
    if "page" not in session:
        session["page"] = "/tablica_rastvorimosti"
        session.modified = True
    session["page"] = "/tablica_rastvorimosti"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # таблица растворимости
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template("tablica_rastvorimosti.html", user=user)
    else:
        return render_template("tablica_rastvorimosti_tat.html", user=user)


@app.route("/tablica_kislotnosti", methods=["GET", "POST"])
def tablica_kislotnosti():
    if "page" not in session:
        session["page"] = "/tablica_kislotnosti"
        session.modified = True
    session["page"] = "/tablica_kislotnosti"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # таблица кислот ( ошибка в названии функции ) :))
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template("tablica_kislotnosti.html", user=user)
    else:
        return render_template("tablica_kislotnosti_tat.html", user=user)


@app.route("/sw.js")
def service_worker():
    return send_from_directory(app.static_folder, "sw.js")


@app.route("/manifest.json")
def manifest():
    return send_from_directory(app.static_folder, "manifest.json")


@app.route("/uchebnik", methods=["GET", "POST"])
def uchebnik():
    if "page" not in session:
        session["page"] = "/uchebnik"
        session.modified = True
    session["page"] = "/uchebnik"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # я не знаю почему учебник, но это просто страница со справочным материалом по органике
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template("uchebnik.html", user=user)
    else:
        return render_template("uchebnik_tat.html", user=user)


@app.route("/glossary_of_chemistry_terms")
def glossarium():
    if "page" not in session:
        session["page"] = "/glossary_of_chemistry_terms"
        session.modified = True
    session["page"] = "/glossary_of_chemistry_terms"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    if session["language"] == "Ru":
        return render_template("glossary.html", user=user)
    else:
        return render_template("glossary_tat.html", user=user)


@app.route("/experiments", methods=["GET", "POST"])
def experiments():
    if "page" not in session:
        session["page"] = "/experiments"
        session.modified = True
    session["page"] = "/experiments"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    if session["language"] == "Ru":
        experiments_data = {
            "acid-base-solutions": "Кислотно-основные растворы",
            "atomic-interactions": "Атомные взаимодействия",
            "balancing-chemical-equations": "Уравнивание химических уравнений",
            "balloons-and-static-electricity": "Воздушные шары и статическое электричество",
            "beers-law-lab": "Лаборатория закона Бера",
            "blackbody-spectrum": "Спектр абсолютно чёрного тела",
            "build-a-molecule": "Построение молекулы",
            "build-a-nucleus": "Построение ядра атома",
            "build-an-atom": "Построение атома",
            "concentration": "Концентрация растворов",
            "coulombs-law": "Закон Кулона",
            "density": "Плотность веществ",
            "diffusion": "Диффузия",
            "energy-forms-and-changes": "Формы и превращения энергии",
            "fourier-making-waves": "Волны Фурье",
            "gas-properties": "Свойства газов",
            "gases-intro": "Введение в газы",
            "isotopes-and-atomic-mass": "Изотопы и атомная масса",
            "models-of-the-hydrogen-atom": "Модели атома водорода",
            "molarity": "Молярность",
            "molecule-polarity": "Полярность молекул",
            "molecule-shapes-basics": "Формы молекул (основы)",
            "molecule-shapes": "Формы молекул",
            "molecules-and-light": "Молекулы и свет",
            "ph-scale-basics": "Шкала pH (основы)",
            "ph-scale": "Шкала pH",
            "reactants-products-and-leftovers": "Реагенты, продукты и остатки",
            "rutherford-scattering": "Опыт Резерфорда",
            "states-of-matter-basics": "Агрегатные состояния (основы)",
            "states-of-matter": "Агрегатные состояния",
            "wave-on-a-string": "Волна на струне",
        }

        # Для обратной совместимости сохраняем и исходный список
        all_experiments = list(experiments_data.keys())

        return render_template(
            "experiments.html",
            user=user,
            all_experiments=all_experiments,
            experiments_data=experiments_data,
        )
    else:
        experiments_data = {
            "acid-base-solutions": "Кислотно-основные растворы",
            "atomic-interactions": "Атомные взаимодействия",
            "balancing-chemical-equations": "Уравнивание химических уравнений",
            "balloons-and-static-electricity": "Воздушные шары и статическое электричество",
            "beers-law-lab": "Лаборатория закона Бера",
            "blackbody-spectrum": "Спектр абсолютно чёрного тела",
            "build-a-molecule": "Построение молекулы",
            "build-a-nucleus": "Построение ядра атома",
            "build-an-atom": "Построение атома",
            "concentration": "Концентрация растворов",
            "coulombs-law": "Закон Кулона",
            "density": "Плотность веществ",
            "diffusion": "Диффузия",
            "energy-forms-and-changes": "Формы и превращения энергии",
            "fourier-making-waves": "Волны Фурье",
            "gas-properties": "Свойства газов",
            "gases-intro": "Введение в газы",
            "isotopes-and-atomic-mass": "Изотопы и атомная масса",
            "models-of-the-hydrogen-atom": "Модели атома водорода",
            "molarity": "Молярность",
            "molecule-polarity": "Полярность молекул",
            "molecule-shapes-basics": "Формы молекул (основы)",
            "molecule-shapes": "Формы молекул",
            "molecules-and-light": "Молекулы и свет",
            "ph-scale-basics": "Шкала pH (основы)",
            "ph-scale": "Шкала pH",
            "reactants-products-and-leftovers": "Реагенты, продукты и остатки",
            "rutherford-scattering": "Опыт Резерфорда",
            "states-of-matter-basics": "Агрегатные состояния (основы)",
            "states-of-matter": "Агрегатные состояния",
            "wave-on-a-string": "Волна на струне",
        }

        # Для обратной совместимости сохраняем и исходный список
        all_experiments = list(experiments_data.keys())

        return render_template(
            "experiments_tat.html",
            user=user,
            all_experiments=all_experiments,
            experiments_data=experiments_data,
        )


@app.route("/experiments/<exp_name>", methods=["GET", "POST"])
def experiment_page(exp_name):
    # страница для каждого эксперимента(отдельная)
    if (
        exp_name != "build-a-molecule"
        or exp_name != "models-of-the-hydrogen-atom"
    ):
        return send_from_directory(
            "templates/onlinelabs", f"{exp_name}_ru.html"
        )
    elif (
        exp_name == "build-a-molecule"
        or exp_name == "models-of-the-hydrogen-atom"
    ):
        return send_from_directory(
            "templates/onlinelabs", f"{exp_name}_en.html"
        )


def get_electron_config(atomic_number):
    # функция повторяет суть функции electronic_confuguration, но есть небольшие различия. В будущем нужно будет переписать чтобы не повторять одну и ту же ф-цию дважды
    elements_by_number = {
        1: "H",
        2: "He",
        3: "Li",
        4: "Be",
        5: "B",
        6: "C",
        7: "N",
        8: "O",
        9: "F",
        10: "Ne",
        11: "Na",
        12: "Mg",
        13: "Al",
        14: "Si",
        15: "P",
        16: "S",
        17: "Cl",
        18: "Ar",
        19: "K",
        20: "Ca",
        21: "Sc",
        22: "Ti",
        23: "V",
        24: "Cr",
        25: "Mn",
        26: "Fe",
        27: "Co",
        28: "Ni",
        29: "Cu",
        30: "Zn",
        31: "Ga",
        32: "Ge",
        33: "As",
        34: "Se",
        35: "Br",
        36: "Kr",
        37: "Rb",
        38: "Sr",
        39: "Y",
        40: "Zr",
        41: "Nb",
        42: "Mo",
        43: "Tc",
        44: "Ru",
        45: "Rh",
        46: "Pd",
        47: "Ag",
        48: "Cd",
        49: "In",
        50: "Sn",
        51: "Sb",
        52: "Te",
        53: "I",
        54: "Xe",
        55: "Cs",
        56: "Ba",
        57: "La",
        58: "Ce",
        59: "Pr",
        60: "Nd",
        61: "Pm",
        62: "Sm",
        63: "Eu",
        64: "Gd",
        65: "Tb",
        66: "Dy",
        67: "Ho",
        68: "Er",
        69: "Tm",
        70: "Yb",
        71: "Lu",
        72: "Hf",
        73: "Ta",
        74: "W",
        75: "Re",
        76: "Os",
        77: "Ir",
        78: "Pt",
        79: "Au",
        80: "Hg",
        81: "Tl",
        82: "Pb",
        83: "Bi",
        84: "Po",
        85: "At",
        86: "Rn",
        87: "Fr",
        88: "Ra",
        89: "Ac",
        90: "Th",
        91: "Pa",
        92: "U",
        93: "Np",
        94: "Pu",
        95: "Am",
        96: "Cm",
        97: "Bk",
        98: "Cf",
        99: "Es",
        100: "Fm",
        101: "Md",
        102: "No",
        103: "Lr",
        104: "Rf",
        105: "Db",
        106: "Sg",
        107: "Bh",
        108: "Hs",
        109: "Mt",
        110: "Ds",
        111: "Rg",
        112: "Cn",
        113: "Nh",
        114: "Fl",
        115: "Mc",
        116: "Lv",
        117: "Ts",
        118: "Og",
    }

    element = elements_by_number.get(atomic_number if atomic_number else "")
    if not element:
        return None, None

    # Порядок заполнения орбиталей (правило Клечковского) https://ru.wikipedia.org/wiki/Правило_Клечковского
    orbitals = [
        {"sub": "1s", "max": 2},
        {"sub": "2s", "max": 2},
        {"sub": "2p", "max": 6},
        {"sub": "3s", "max": 2},
        {"sub": "3p", "max": 6},
        {"sub": "4s", "max": 2},
        {"sub": "3d", "max": 10},
        {"sub": "4p", "max": 6},
        {"sub": "5s", "max": 2},
        {"sub": "4d", "max": 10},
        {"sub": "5p", "max": 6},
        {"sub": "6s", "max": 2},
        {"sub": "4f", "max": 14},
        {"sub": "5d", "max": 10},
        {"sub": "6p", "max": 6},
        {"sub": "7s", "max": 2},
        {"sub": "5f", "max": 14},
        {"sub": "6d", "max": 10},
        {"sub": "7p", "max": 6},
        {"sub": "8s", "max": 2},
    ]

    config = []
    remaining = atomic_number

    for orb in orbitals:
        if remaining <= 0:
            break
        electrons = min(orb["max"], remaining)
        config.append(
            {
                "subshell": orb["sub"],
                "electrons": electrons,
                "type": orb["sub"][1],
                "level": int(orb["sub"][0]),
            }
        )
        remaining -= electrons

    return config


@app.route("/element/<int:id>")
def about_elements(id):
    if "page" not in session:
        session["page"] = f"/element/{id}"
        session.modified = True
    session["page"] = f"/element/{id}"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user
    elements_list = [
        "H",
        "He",
        "Li",
        "Be",
        "B",
        "C",
        "N",
        "O",
        "F",
        "Ne",
        "Na",
        "Mg",
        "Al",
        "Si",
        "P",
        "S",
        "Cl",
        "Ar",
        "K",
        "Ca",
        "Sc",
        "Ti",
        "V",
        "Cr",
        "Mn",
        "Fe",
        "Co",
        "Ni",
        "Cu",
        "Zn",
        "Ga",
        "Ge",
        "As",
        "Se",
        "Br",
        "Kr",
        "Rb",
        "Sr",
        "Y",
        "Zr",
        "Nb",
        "Mo",
        "Tc",
        "Ru",
        "Rh",
        "Pd",
        "Ag",
        "Cd",
        "In",
        "Sn",
        "Sb",
        "Te",
        "I",
        "Xe",
        "Cs",
        "Ba",
        "La",
        "Ce",
        "Pr",
        "Nd",
        "Pm",
        "Sm",
        "Eu",
        "Gd",
        "Tb",
        "Dy",
        "Ho",
        "Er",
        "Tm",
        "Yb",
        "Lu",
        "Hf",
        "Ta",
        "W",
        "Re",
        "Os",
        "Ir",
        "Pt",
        "Au",
        "Hg",
        "Tl",
        "Pb",
        "Bi",
        "Po",
        "At",
        "Rn",
        "Fr",
        "Ra",
        "Ac",
        "Th",
        "Pa",
        "U",
        "Np",
        "Pu",
        "Am",
        "Cm",
        "Bk",
        "Cf",
        "Es",
        "Fm",
        "Md",
        "No",
        "Lr",
        "Rf",
        "Db",
        "Sg",
        "Bh",
        "Hs",
        "Mt",
        "Ds",
        "Rg",
        "Cn",
        "Nh",
        "Fl",
        "Mc",
        "Lv",
        "Ts",
        "Og",
    ]
    if 0 < id <= 118:
        with open("src/static/elements_normal.json", "r", encoding="utf-8") as f:
            parsed_data = json.load(f)
        data = parsed_data[str(id)]
        period = 0
        if 1 <= id <= 2:
            period = 1
        elif 3 <= id <= 10:
            period = 2
        elif 11 <= id <= 18:
            period = 3
        elif 19 <= id <= 36:
            period = 4
        elif 37 <= id <= 54:
            period = 5
        elif 55 <= id <= 86:
            period = 6
        elif 87 <= id <= 118:
            period = 7
        group = 0
        if (
            id == 1
            or id == 3
            or id == 11
            or id == 19
            or id == 29
            or id == 37
            or id == 47
            or id == 55
            or id == 79
            or id == 87
        ):
            group = 1
        elif (
            id == 4
            or id == 12
            or id == 20
            or id == 30
            or id == 38
            or id == 48
            or id == 56
            or id == 80
            or id == 88
        ):
            group = 2
        elif (
            id == 5
            or id == 13
            or id == 21
            or id == 31
            or id == 39
            or id == 49
            or 57 <= id <= 71
            or id == 81
            or 89 <= id <= 103
        ):
            group = 3
        elif (
            id == 6
            or id == 14
            or id == 22
            or id == 32
            or id == 40
            or id == 50
            or id == 72
            or id == 82
            or id == 104
        ):
            group = 4
        elif (
            id == 7
            or id == 15
            or id == 23
            or id == 33
            or id == 41
            or id == 51
            or id == 73
            or id == 83
            or id == 105
        ):
            group = 5
        elif (
            id == 8
            or id == 16
            or id == 24
            or id == 34
            or id == 42
            or id == 52
            or id == 74
            or id == 84
        ):
            group = 6
        elif (
            id == 9
            or id == 17
            or id == 25
            or id == 35
            or id == 43
            or id == 53
            or id == 75
            or id == 85
        ):
            group = 7
        else:
            group = 8
        atomicnumber = id
        symbol = data["Symbol"]
        config = (
            get_electron_config(atomicnumber) if atomicnumber else (None, None)
        )
        name = data["Name"]
        atomicmass = data["AtomicMass"]
        cpxhexcolor = data["CPKHexColor"]
        electronicconfiguration = data["ElectronConfiguration"]
        electronegativity = data["Electronegativity"]
        atomicradius = data["AtomicRadius"]
        ionizationenergy = data["IonizationEnergy"]
        electronaffinity = data["ElectronAffinity"]
        oxidationstates = data["OxidationStates"]
        standartstate = data["StandardState"]
        meltingpoint = data["MeltingPoint"]
        boilingpoint = data["BoilingPoint"]
        density = data["Density"]
        groupblock = data["GroupBlock"]
        year = data["YearDiscovered"]
        if session["language"] == "Ru":
            return render_template(
                "about_elements.html",
                user=user,
                symbol=symbol,
                name=name,
                period=period,
                group=group,
                atomicnumber=int(atomicnumber),
                atomicmass=float(atomicmass),
                cpxhexcolor=cpxhexcolor,
                electronicconfiguration=electronicconfiguration,
                electronegativity=electronegativity,
                atomicradius=atomicradius,
                ionizationenergy=ionizationenergy,
                electronaffinity=electronaffinity,
                oxidationstates=oxidationstates,
                standartstate=standartstate,
                meltingpoint=meltingpoint,
                boilingpoint=boilingpoint,
                density=density,
                groupblock=groupblock,
                year=year,
                config=config,
                current_element=symbol if symbol else None,
            )
        else:
            return render_template(
                "about_elements_tat.html",
                user=user,
                symbol=symbol,
                name=name,
                period=period,
                group=group,
                atomicnumber=int(atomicnumber),
                atomicmass=float(atomicmass),
                cpxhexcolor=cpxhexcolor,
                electronicconfiguration=electronicconfiguration,
                electronegativity=electronegativity,
                atomicradius=atomicradius,
                ionizationenergy=ionizationenergy,
                electronaffinity=electronaffinity,
                oxidationstates=oxidationstates,
                standartstate=standartstate,
                meltingpoint=meltingpoint,
                boilingpoint=boilingpoint,
                density=density,
                groupblock=groupblock,
                year=year,
                config=config,
                current_element=symbol if symbol else None,
            )
    else:
        bugcode = 10
        return render_template("bug.html", user=user, bugcode=bugcode)


def minigamefunc():
    # функция обработчик миниигры
    a = random.randint(0, 117)
    atomic_masses = {
        "H": "Водород",
        "He": "Гелий",
        "Li": "Литий",
        "Be": "Бериллий",
        "B": "Бор",
        "C": "Углерод",
        "N": "Азот",
        "O": "Кислород",
        "F": "Фтор",
        "Ne": "Неон",
        "Na": "Натрий",
        "Mg": "Магний",
        "Al": "Алюминий",
        "Si": "Кремний",
        "P": "Фосфор",
        "S": "Сера",
        "Cl": "Хлор",
        "Ar": "Аргон",
        "K": "Калий",
        "Ca": "Кальций",
        "Sc": "Скандий",
        "Ti": "Титан",
        "V": "Ванадий",
        "Cr": "Хром",
        "Mn": "Марганец",
        "Fe": "Железо",
        "Co": "Кобальт",
        "Ni": "Никель",
        "Cu": "Медь",
        "Zn": "Цинк",
        "Ga": "Галлий",
        "Ge": "Германий",
        "As": "Мышьяк",
        "Se": "Селен",
        "Br": "Бром",
        "Kr": "Криптон",
        "Rb": "Рубидий",
        "Sr": "Стронций",
        "Y": "Иттрий",
        "Zr": "Цирконий",
        "Nb": "Ниобий",
        "Mo": "Молибден",
        "Tc": "Технеций",
        "Ru": "Рутений",
        "Rh": "Родий",
        "Pd": "Палладий",
        "Ag": "Серебро",
        "Cd": "Кадмий",
        "In": "Индий",
        "Sn": "Олово",
        "Sb": "Сурьма",
        "Te": "Теллур",
        "I": "Йод",
        "Xe": "Ксенон",
        "Cs": "Цезий",
        "Ba": "Барий",
        "La": "Лантан",
        "Ce": "Церий",
        "Pr": "Празеодим",
        "Nd": "Неодим",
        "Pm": "Прометий",
        "Sm": "Самарий",
        "Eu": "Европий",
        "Gd": "Гадолиний",
        "Tb": "Тербий",
        "Dy": "Диспрозий",
        "Ho": "Гольмий",
        "Er": "Эрбий",
        "Tm": "Тулий",
        "Yb": "Иттербий",
        "Lu": "Лютеций",
        "Hf": "Гафний",
        "Ta": "Тантал",
        "W": "Вольфрам",
        "Re": "Рений",
        "Os": "Осмий",
        "Ir": "Иридий",
        "Pt": "Платина",
        "Au": "Золото",
        "Hg": "Ртуть",
        "Tl": "Таллий",
        "Pb": "Свинец",
        "Bi": "Висмут",
        "Po": "Полоний",
        "At": "Астат",
        "Rn": "Радон",
        "Fr": "Франций",
        "Ra": "Радий",
        "Ac": "Актиний",
        "Th": "Торий",
        "Pa": "Проактиний",
        "U": "Уран",
        "Np": "Нептуний",
        "Pu": "Плутоний",
        "Am": "Америций",
        "Cm": "Кюрий",
        "Bk": "Берклий",
        "Cf": "Калифорний",
        "Es": "Эйнштейний",
        "Fm": "Фермий",
        "Md": "Менделевий",
        "No": "Нобелий",
        "Lr": "Лоуренсий",
        "Rf": "Резерфордий",
        "Db": "Дубний",
        "Sg": "Сиборгий",
        "Bh": "Борий",
        "Hs": "Хассий",
        "Mt": "Майтнерий",
        "Ds": "Дармштадтий",
        "Rg": "Рентгений",
        "Cn": "Коперниций",
        "Nh": "Нихоний",
        "Fl": "Флеровий",
        "Mc": "Московий",
        "Lv": "Ливерморий",
        "Ts": "Теннессин",
        "Og": "Оганессон",
    }
    k = []
    d = ""
    b = ""
    for i in atomic_masses:
        k.append(i)
    b = k[a]
    nazv = atomic_masses[b]
    return b, nazv


@app.route("/minigame", methods=["GET", "POST"])
def minigame():
    if "page" not in session:
        session["page"] = "/minigame"
        session.modified = True
    session["page"] = "/minigame"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # функция, которая возвращает страницу мини-игры
    d = ""
    user = flask_login.current_user

    # Получаем или создаём состояние игры для пользователя
    if user.is_authenticated:
        game_state = UserGameState.query.filter_by(
            user_id=user.username
        ).first()

        if not game_state:
            game_state = UserGameState(
                user_id=user.username, answer_list=""
            )  # Инициализируем список
            db.session.add(game_state)
            db.session.commit()

        res = minigamefunc()
        b = res[0]
        nazv = res[1]

        # Добавляем название элемента в answer_list
        game_state.answer_list = str(game_state.answer_list)
        game_state.answer_list += f" {nazv}"

        # Сохраняем изменения после добавления
        db.session.commit()

        # Повторное извлечение состояния игры
        game_state = UserGameState.query.filter_by(
            user_id=user.username
        ).first()

        if user.is_authenticated and user.username == game_state.user_id:
            if request.method == "POST":
                element = request.form["element"]

                if element.capitalize() == game_state.answer_list.split()[-2]:
                    d = "Верно, следующий"
                    user.pokupki += 1
                    user.summa += 1
                    game_state.correct_answers = user.pokupki
                    game_state.total_answers = user.summa
                    db.session.commit()

                    if game_state.total_answers >= 10 and user.pokupki >= 10:
                        right_percent = round(
                            (
                                game_state.correct_answers
                                / game_state.total_answers
                            )
                            * 100,
                            2,
                        )
                        user.summa = 0
                        user.pokupki = 0
                        game_state.correct_answers = user.pokupki
                        game_state.total_answers = user.summa

                        if right_percent >= 50:
                            user.wins += 1
                            user.allgames += 1
                        else:
                            user.allgames += 1

                        # Обнуляем answer_list
                        game_state.answer_list = (
                            ""  # Здесь мы обнуляем answer_list
                        )
                        db.session.commit()  # Сохраняем изменения
                        if session["language"] == "Ru":
                            return render_template(
                                "winning.html",
                                user=user,
                                right_percent=right_percent,
                            )
                        else:
                            return render_template(
                                "winning_tat.html",
                                user=user,
                                right_percent=right_percent,
                            )
                else:
                    d = f"Неправильно, ответ: {game_state.answer_list.split()[-2]}"
                    game_state.total_answers += 1
                    user.summa += 1
                    db.session.commit()
            if session["language"] == "Ru":
                return render_template(
                    "minigame.html",
                    user=user,
                    d=d,
                    minigamefunc=minigamefunc,
                    b=b,
                    pravilno=game_state.correct_answers,
                    otvety=game_state.total_answers,
                )
            else:
                return render_template(
                    "minigame_tat.html",
                    user=user,
                    d=d,
                    minigamefunc=minigamefunc,
                    b=b,
                    pravilno=game_state.correct_answers,
                    otvety=game_state.total_answers,
                )

    else:
        return redirect(url_for("login"))


@app.route("/reset_minigame", methods=["GET", "POST"])
def reset_minigame():
    # сброс статистики миниигры. добавляется +1 к игре и сбрасывается вся статистика
    user = flask_login.current_user
    game_state = UserGameState.query.filter_by(user_id=user.username).first()
    if user.username == game_state.user_id:
        user.allgames += 1
        game_state.answer_list = ""
        game_state.total_answers = 0
        game_state.correct_answers = 0
        user.summa = 0
        user.pokupki = 0
        db.session.commit()
        return redirect(url_for("minigame"))
    else:
        bugcode = 9
        return render_template("bug.html", user=user, bugcode=bugcode)


def get_substance_html(substance_name):
    # получение имени орг вещества из таблицы на сайте при помощи парсинга этой страницы
    url = "https://chemer.ru/services/organic/structural"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url)
    global klass
    klass = ""
    namez = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        rows = table.find_all("tr")

        for row in rows:
            cols = row.find_all("td")
            if cols:
                name = cols[0].text.strip()
                klass = cols[1].text.strip()
                link = cols[0].find("a")["href"]
                if (
                    substance_name.lower() in name.lower()
                    and substance_name.lower() == name.lower()
                ):
                    substance_url = (
                        f"https://chemer.ru/services/organic/{link}"
                    )
                    substance_response = session.get(substance_url)
                    return substance_response.text, None
                elif (
                    substance_name.lower() in name.lower()
                    and name.lower()[2:] != substance_name.lower()
                ):
                    namez.append(name)
                elif (
                    substance_name.lower() in name.lower()
                    and name.lower()[:2] == "н-"
                    and name.lower()[2:] == substance_name.lower()
                ):
                    substance_url = (
                        f"https://chemer.ru/services/organic/{link}"
                    )
                    substance_response = session.get(substance_url)
                    return substance_response.text, None
    return None, namez


def extract_svg_and_symbols(html_code):
    # занимается сохранением свг-картинок на сервер
    soup = BeautifulSoup(html_code, "html.parser")
    svg_elements = soup.find_all("svg")
    symbols = soup.find_all("symbol")
    names = ""

    if not svg_elements:
        return None, None, None

    first_svg_content = str(svg_elements[0])
    if "width" not in first_svg_content or "height" not in first_svg_content:
        first_svg_content = first_svg_content.replace(
            "<svg", '<svg width="200" height="200"'
        )

    isomer_svgs = []
    spacing = 220  # Расстояние между изомерами
    max_per_row = 20  # Максимум изомеров в строке

    # Извлечение секции с id='tab1'
    tab1_section = soup.find("section", id="tab1")

    if tab1_section:
        # Получаем все SVG элементы внутри секции
        svg_elements2 = tab1_section.find_all("svg")
        names = tab1_section.find_all("a")

        for index, svg in enumerate(svg_elements2):
            row = index // max_per_row  # Определяем номер строки
            col = index % max_per_row  # Определяем номер колонки
            x = col - 1  # Устанавливаем x координату
            y = row  # Устанавливаем y координату для новой строки
            svg_str = str(svg).replace(
                "<svg", f'<svg x="{x}" y="{y}"'
            )  # Устанавливаем координаты
            isomer_svgs.append(svg_str)

    isomer_svgs_content = "".join(isomer_svgs)
    symbol_content = "".join(str(symbol) for symbol in symbols)

    return first_svg_content, isomer_svgs_content, symbol_content, names


@app.route("/orghim", methods=["GET", "POST"])
def orghim():
    if "page" not in session:
        session["page"] = "/orghim"
        session.modified = True
    session["page"] = "/orghim"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # основная страница для работы с методами(предыдущими двумя). Все вместе это ф-ция орг.химии
    # ее суть в выведении названий веществ и картинок изомеров и самого вещества
    # изомеров только 10, т.к 70 изомеров декана, например, может сильно нагрузить устройство пользователя и сервер,
    # который может обрабатывать несколько таких запросов, что приведет к замедлению его работы(он и так бесплатный)
    global klass
    combined = ""
    isomer_files = []
    variants = ""
    user = flask_login.current_user
    substance_name = ""
    if request.method == "POST":
        substance_name = request.form["substance_name"]
        html_code, variants = get_substance_html(substance_name)

        if html_code:
            first_svg, isomers_svg, symbols_svg, names = (
                extract_svg_and_symbols(html_code)
            )

            # Сохраняем первую SVG-картинку и символы в файл
            if first_svg:
                with open("static/output.svg", "w", encoding="utf-8") as f:
                    f.write(
                        f"<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>{symbols_svg}{first_svg}</svg>"
                    )

            # Сохраняем изомеры в отдельные файлы
            if isomers_svg.strip():
                isomer_files = []
                nazvaniya = []
                for index, svg in enumerate(isomers_svg.split("</svg>")):
                    if index <= 9:
                        if svg.strip():
                            file_name = f"static/isomer_{index}.svg"
                            with open(file_name, "w", encoding="utf-8") as f:
                                f.write(
                                    f"<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>Х{symbols_svg}{svg}</svg></svg>"
                                )
                            filename_without_static = f"isomer_{index}.svg"
                            isomer_files.append(filename_without_static)

                for i, nazv in enumerate(names):
                    if i <= 9:
                        soup = BeautifulSoup(str(nazv), "html.parser")
                        nazv = soup.a.text
                        nazvaniya.append(nazv.capitalize())
                combined = list(zip(nazvaniya, isomer_files))

            if session["language"] == "Ru":
                return render_template(
                    "orghim.html",
                    svg_file="output.svg",
                    isomer_files=isomer_files,
                    substance_name=substance_name,
                    user=user,
                    klass=klass,
                    combined=combined,
                )
            else:
                return render_template(
                    "orghim_tat.html",
                    svg_file="output.svg",
                    isomer_files=isomer_files,
                    substance_name=substance_name,
                    user=user,
                    klass=klass,
                    combined=combined,
                )
    if session["language"] == "Ru":
        return render_template(
            "orghim.html",
            svg_file=None,
            isomer_files=None,
            nazvaniya=None,
            user=user,
            variants=variants,
            substance_name=substance_name,
        )
    else:
        return render_template(
            "orghim_tat.html",
            svg_file=None,
            isomer_files=None,
            nazvaniya=None,
            user=user,
            variants=variants,
            substance_name=substance_name,
        )


@app.errorhandler(404)
def page_not_found(e):
    # просто обработчик ошибок, нужен, чтобы говорить пользователю, что такой страницы нет
    user = flask_login.current_user
    bugcode = 6
    return render_template("bug.html", user=user, bugcode=bugcode), 404


bugcode = 0


@app.route("/login", methods=["GET", "POST"])
def login():
    if "page" not in session:
        session["page"] = "/login"
        session.modified = True
    session["page"] = "/login"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    bugcode = 0
    # вход пользователя в аккаунт. берутся данные из базы данных
    user = flask_login.current_user
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            flask_login.login_user(user)
            return redirect("/")
        elif not User.query.filter_by(username=username).first():
            bugcode = 1
            return render_template("bug.html", bugcode=bugcode, user=user)
        else:
            bugcode = 2
            user = ""
            return render_template("bug.html", bugcode=bugcode, user=user)
    if user.is_authenticated:
        return redirect(url_for("profile"))
    else:
        if session["language"] == "Ru":
            return render_template("login.html", user=user)
        else:
            return render_template("login_tat.html", user=user)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.request_loader
def load_user_from_request(request):
    user_id = request.args.get("user_id")
    if user_id:
        return User.query.get(user_id)
    return None


@app.route("/register", methods=["GET", "POST"])
def register():
    if "page" not in session:
        session["page"] = "/register"
        session.modified = True
    session["page"] = "/register"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    bugcode = 0
    # регистрация, идет работа с бд
    user = flask_login.current_user
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        name = request.form["name"]
        surname = request.form["surname"]
        email = request.form["email"]
        if not User.query.filter_by(username=username).first():
            if password == confirm_password:
                user = User(
                    username=username, name=name, surname=surname, email=email
                )
                user.set_password(password)
                try:
                    db.session.add(user)
                    db.session.commit()
                    return redirect(url_for("login"))
                except:
                    bugcode = 4
                    return render_template(
                        "bug.html", bugcode=bugcode, user=user
                    )
            else:
                bugcode = 5
                return render_template("bug.html", bugcode=bugcode, user=user)
        elif User.query.filter_by(username=username).first():
            bugcode = 3
            return render_template("bug.html", bugcode=bugcode, user=user)
        else:
            bugcode = 4
            return render_template("bug.html", bugcode=bugcode, user=user)
    if session["language"] == "Ru":
        return render_template("register.html", user=user)
    else:
        return render_template("register_tat.html", user=user)


@app.route("/profile")
def profile():
    if "page" not in session:
        session["page"] = "/profile"
        session.modified = True
    session["page"] = "/profile"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # профиль
    user = flask_login.current_user
    if user.is_authenticated:
        if session["language"] == "Ru":
            return render_template("profile.html", user=user)
        else:
            return render_template("profile_tat.html", user=user)
    else:
        return redirect(url_for("login"))


@app.route("/delete_account/<username>", methods=["GET", "POST"])
def delete_profile(username):
    # удаление профилей пользователей
    user = flask_login.current_user
    bugcode = 0
    polzovatel = User.query.filter_by(username=username).first()
    if user.is_authenticated:
        if user.admin == 1 or user.username == polzovatel.username:
            try:
                filename = polzovatel.avatar
                db.session.delete(polzovatel)
                db.session.commit()
                if filename != "default_avatar.png":
                    avatar_path = os.path.join(
                        app.config["UPLOAD_FOLDER"], filename
                    )
                    if os.path.exists(avatar_path):
                        os.remove(avatar_path)
            except:
                bugcode = 8
                return render_template("bug.html", user=user, bugcode=bugcode)
            if user.admin == 1:
                return redirect(url_for("all_profiles"))
            else:
                return redirect(url_for("login"))
    else:
        return redirect(url_for("login"))


@app.route("/profile/<username>", methods=["POST", "GET"])
def other_profiles(username):
    if "page" not in session:
        session["page"] = f"/profile/{username}"
        session.modified = True
    session["page"] = f"/profile/{username}"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # профили других людей
    polzovatel = User.query.filter_by(username=username).first()
    user = flask_login.current_user

    if polzovatel:
        admin = polzovatel.admin
        if polzovatel != user:
            if session["language"] == "Ru":
                return render_template(
                    "otherprofile.html",
                    user=user,
                    polzovatel=polzovatel,
                    admin=admin,
                )
            else:
                return render_template(
                    "otherprofile_tat.html",
                    user=user,
                    polzovatel=polzovatel,
                    admin=admin,
                )
        else:
            if session["language"] == "Ru":
                return render_template("profile.html", user=user)
            else:
                return render_template("profile_tat.html", user=user)
    else:
        bugcode = 7
        return render_template("bug.html", user=user, bugcode=bugcode)


@app.route("/profile/<username>/make_admin", methods=["GET", "POST"])
def make_admin(username):
    # возможность одного админа присвоить админку другому. удалению возможно только вручную через бд
    polzovatel = User.query.filter_by(username=username).first()
    user = flask_login.current_user
    admin = polzovatel.admin
    if user.admin == 1:
        polzovatel.admin = 1
        db.session.commit()
        return render_template(
            "otherprofile.html", user=user, polzovatel=polzovatel, admin=admin
        )
    else:
        bugcode = 6
        return render_template("bug.html", user=user, bugcode=bugcode)


@app.route("/all_profiles/", methods=["GET", "POST"])
def all_profiles():
    if "page" not in session:
        session["page"] = "/all_profiles"
        session.modified = True
    session["page"] = "/all_profiles"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    # функция, которая выводит список всех пользователей сайта
    user = flask_login.current_user
    polzovatel = User.query.all()
    if session["language"] == "Ru":
        return render_template(
            "all_profiles.html", user=user, polzovatel=polzovatel
        )
    else:
        return render_template(
            "all_profiles_tat.html", user=user, polzovatel=polzovatel
        )


# Функция загрузки файла на Яндекс.Диск
def upload_to_yandex_disk(file_path, filename):
    # Источник доступа к API
    token = os.getenv("YANDEX_TOKEN")
    headers = {"Authorization": f"OAuth {token}"}
    # URL для загрузки файла
    upload_url = f"https://cloud-api.yandex.net/v1/disk/resources/upload?path=users_avatars/{filename}&overwrite=true"
    response = requests.get(upload_url, headers=headers)

    if response.status_code == 200:
        upload_link = response.json().get("href")
        with open(file_path, "rb") as f:
            requests.put(upload_link, data=f)
        return True
    return False


@app.route("/edit_profile", methods=["GET", "POST"])
@flask_login.login_required
def edit_profile():
    if "page" not in session:
        session["page"] = "/edit_profile"
        session.modified = True
    session["page"] = "/edit_profile"
    session.modified = True
    if "language" not in session:
        session["language"] = "Ru"
        session.modified = True
    user = flask_login.current_user

    if request.method == "POST":
        # Получение данных из формы
        username = request.form["username"]
        name = request.form["name"]
        surname = request.form["surname"]
        email = request.form["email"]
        status = request.form["status"]
        checking = User.query.filter_by(username=username).first()

        if checking and checking.id != user.id:
            bugcode = 4
            return render_template("bug.html", user=user, bugcode=bugcode)

        user.username = username
        user.name = name
        user.surname = surname
        user.email = email
        user.status = status

        # Загрузка аватара
        if "avatar" in request.files:
            file = request.files["avatar"]
            if file and file.filename != "":
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)  # Локальное сохранение файла на сервер

                # Загружаем файл на Yandex.Disk
                if upload_to_yandex_disk(file_path, filename):
                    user.avatar = filename  # Сохраняем имя файла в БД

        try:
            db.session.commit()
            return redirect(url_for("profile"))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for("edit_profile"))
    if session["language"] == "Ru":
        return render_template("edit_profile.html", user=user)
    else:
        return render_template("edit_profile_tat.html", user=user)


with app.app_context():
    db.create_all()


@app.route("/logout")
@flask_login.login_required
def logout():
    # выход из аккаунта
    flask_login.logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    try:
        app.run(debug=True, host="0.0.0.0", port=5000)
    finally:
        scheduler.shutdown()
