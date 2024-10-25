from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify, send_file
import re
from mod import db, User
from chempy import balance_stoichiometry
import os
import flask_login
import json
from flask_login import login_required, UserMixin, LoginManager, login_user
from werkzeug.utils import secure_filename
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import random
from datetime import datetime
# импортируем все библиотеки

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/upload'
app.secret_key = 'supersecretkey'
login_manager = LoginManager()
login_manager.init_app(app)
db.init_app(app)
c = []


def molecular_mass(formula):
    # Словарь с атомными массами элементов
    atomic_masses = {
        'H': 1.008,
        'He': 4.0026,
        'Li': 6.94,
        'Be': 9.0122,
        'B': 10.81,
        'C': 12.011,
        'N': 14.007,
        'O': 15.999,
        'F': 18.998,
        'Ne': 20.180,
        'Na': 22.99,
        'Mg': 24.305,
        'Al': 26.982,
        'Si': 28.085,
        'P': 30.974,
        'S': 32.06,
        'Cl': 35.45,
        'Ar': 39.948,
        'K': 39.098,
        'Ca': 40.078,
        'Sc': 44.956,
        'Ti': 47.867,
        'V': 50.941,
        'Cr': 51.996,
        'Mn': 54.938,
        'Fe': 55.845,
        'Co': 58.933,
        'Ni': 58.693,
        'Cu': 63.546,
        'Zn': 65.38,
        'Ga': 69.723,
        'Ge': 72.630,
        'As': 74.922,
        'Se': 78.971,
        'Br': 79.904,
        'Kr': 83.798,
        'Rb': 85.468,
        'Sr': 87.62,
        'Y': 88.906,
        'Zr': 91.224,
        'Nb': 92.906,
        'Mo': 95.95,
        'Tc': 98,
        'Ru': 101.07,
        'Rh': 102.905,
        'Pd': 106.42,
        'Ag': 107.868,
        'Cd': 112.414,
        'In': 114.818,
        'Sn': 118.710,
        'Sb': 121.760,
        'Te': 127.60,
        'I': 126.904,
        'Xe': 131.293,
        'Cs': 132.905,
        'Ba': 137.327,
        'La': 138.905,
        'Ce': 140.116,
        'Pr': 140.907,
        'Nd': 144.242,
        'Pm': 145,
        'Sm': 150.36,
        'Eu': 151.964,
        'Gd': 157.25,
        'Tb': 158.925,
        'Dy': 162.500,
        'Ho': 164.930,
        'Er': 167.259,
        'Tm': 168.934,
        'Yb': 173.04,
        'Lu': 174.966,
        'Hf': 178.49,
        'Ta': 180.947,
        'W': 183.84,
        'Re': 186.207,
        'Os': 190.23,
        'Ir': 192.217,
        'Pt': 195.084,
        'Au': 196.967,
        'Hg': 200.592,
        'Tl': 204.38,
        'Pb': 207.2,
        'Bi': 208.980,
        'Po': 209,
        'At': 210,
        'Rn': 222,
        'Fr': 223,
        'Ra': 226,
        'Ac': 227,
        'Th': 232.038,
        'Pa': 231.035,
        'U': 238.028,
        'Np': 237,
        'Pu': 244,
        'Am': 243,
        'Cm': 247,
        'Bk': 247,
        'Cf': 251,
        'Es': 252,
        'Fm': 257,
        'Md': 258,
        'No': 259,
        'Lr': 262,
        'Rf': 267,
        'Db': 270,
        'Sg': 271,
        'Bh': 270,
        'Hs': 277,
        'Mt': 276,
        'Ds': 281,
        'Rg': 282,
        'Cn': 285,
        'Nh': 286,
        'Fl': 289,
        'Mc': 290,
        'Lv': 293,
        'Ts': 294,
        'Og': 294,
    }

    mass = 0.0
    elements = re.findall(r'([A-Z][a-z]?)(\d*)', formula)
    element_details = []  # Список для хранения деталей элементов
    for element, count in elements:
        count = int(count) if count else 1  # Установите 1, если count отсутствует
        element_mass = atomic_masses[element]
        total_mass = element_mass * count
        element_details.append((element, atomic_masses[element], count, total_mass))  # Добавляем элемент, его массу, количество и общую массу
        mass += total_mass

    return round(mass), element_details  # Возвращаем общую массу и детали элементов


def electronic_configuration(element):
    elements_data = {
        'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
        'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19,
        'Ca': 20, 'Sc': 21, 'Ti': 22, 'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28,
        'Cu': 29, 'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36, 'Rb': 37,
        'Sr': 38, 'Y': 39, 'Zr': 40, 'Nb': 41, 'Mo': 42, 'Tc': 43, 'Ru': 44, 'Rh': 45, 'Pd': 46,
        'Ag': 47, 'Cd': 48, 'In': 49, 'Sn': 50, 'Sb': 51, 'Te': 52, 'I': 53, 'Xe': 54, 'Cs': 55,
        'Ba': 56, 'La': 57, 'Ce': 58, 'Pr': 59, 'Nd': 60, 'Pm': 61, 'Sm': 62, 'Eu': 63, 'Gd': 64,
        'Tb': 65, 'Dy': 66, 'Ho': 67, 'Er': 68, 'Tm': 69, 'Yb': 70, 'Lu': 71, 'Hf': 72, 'Ta': 73,
        'W': 74, 'Re': 75, 'Os': 76, 'Ir': 77, 'Pt': 78, 'Au': 79, 'Hg': 80, 'Tl': 81, 'Pb': 82,
        'Bi': 83, 'Po': 84, 'At': 85, 'Rn': 86, 'Fr': 87, 'Ra': 88, 'Ac': 89, 'Th': 90, 'Pa': 91,
        'U': 92, 'Np': 93, 'Pu': 94, 'Am': 95, 'Cm': 96, 'Bk': 97, 'Cf': 98, 'Es': 99, 'Fm': 100,
        'Md': 101, 'No': 102, 'Lr': 103, 'Rf': 104, 'Db': 105, 'Sg': 106, 'Bh': 107, 'Hs': 108,
        'Mt': 109, 'Ds': 110, 'Rg': 111, 'Cn': 112, 'Nh': 113, 'Fl': 114, 'Mc': 115, 'Lv': 116,
        'Ts': 117, 'Og': 118
    }

    atomic_number = elements_data.get(element)
    if element == '':
        return "Введите элемент"
    if atomic_number is None:
        return "Элемент не найден"

    configurations = []
    '''subshells = ['1s', '2s', '2p', '3s', '3p', '4s', '3d', '4p', '5s', '4d', '5p', '6s', '4f', '5d', '6p', '7s', '5f',
                 '6d', '7p']
    electrons = [2, 2, 6, 2, 6, 2, 10, 6, 2, 10, 6, 2, 14, 10, 6, 2, 14, 10, 6]'''
    subshells = ['1s', '2s', '2p', '3s', '3p', '3d', '4s', '4p', '4d', '4f', '5s', '5p', '5d', '5f', '6s', '6p', '6d',
                 '7s', '7p']
    electrons = [2, 2, 6, 2, 6, 10, 2, 6, 10, 14, 2, 6, 10, 14, 2, 6, 10, 2, 6]

    for i in range(len(subshells)):
        if atomic_number > 0:
            if atomic_number >= electrons[i]:
                configurations.append(f"{subshells[i]}^{electrons[i]}")
                atomic_number -= electrons[i]
            else:
                configurations.append(f"{subshells[i]}^{atomic_number}")
                break
    return ' '.join(configurations)


@app.route('/electronic_configuration', methods=['GET', 'POST'])
def electronic_configuration_page():
    # функция, которая отображает страницу электронной конфигурации, предыдущая функция отвечает за обработку ответа
    element = ''
    user = flask_login.current_user
    configuration = ''
    if request.method == 'POST':
        element = request.form.get("element", False)
        configuration = electronic_configuration(element)
    return render_template('electronic_configuration.html', configuration=configuration, user=user, element=element)


def uravnivanie(formula):
    # баланс уравнений
    reactants_input, products_input = formula.split('=')
    reactants = {x.split()[0].strip(): int(x.split()[1]) if len(x.split()) > 1 else 1 for x in
                 reactants_input.split('+')}
    products = {x.split()[0].strip(): int(x.split()[1]) if len(x.split()) > 1 else 1 for x in products_input.split('+')}

    balanced_reaction = balance_stoichiometry(reactants, products)

    reactants_str = ' + '.join([f"{v}{k}" for k, v in balanced_reaction[0].items()])
    products_str = ' + '.join([f"{v}{k}" for k, v in balanced_reaction[1].items()])

    otvet = f"{reactants_str} = {products_str}"

    return otvet


@app.route('/', methods=['GET', 'POST'])
def main():
    #функция, которая возвращает главную страницу сайта( main.html )
    user = flask_login.current_user
    return render_template('main.html', user=user)


@app.route('/uravnivanie', methods=['GET', 'POST'])
def osnova():
    # функция которая возвращает уравнивание хим.реакций( index.html )
    user = flask_login.current_user
    resultat2 = ''
    if request.method == 'POST':
        chemical_formula = request.form['chemical_formula']
        try:
            resultat2 = f'{chemical_formula}: {uravnivanie(chemical_formula)}'
            print(resultat2)
        except:
            redirect('/')
    return render_template('index.html', resultat2=resultat2, user=user)


@app.route('/molyarnaya_massa', methods=['GET', 'POST'])
def molyar_massa():
    # метод для вычисления молярной массы и отображения ее на сайте
    user = flask_login.current_user
    global resultat, dlyproverki, c
    resultat = ''
    otdelno = []
    formatspisok = ''
    dlyproverki = 0
    if request.method == 'POST':
        chemical_formula = request.form['element']
        try:
            dlyproverki, element_details = molecular_mass(chemical_formula)
            resultat = f"Молярная масса {chemical_formula}: {dlyproverki} г/моль"
            for element, mass, count, total_mass in element_details:
                otdelno.append(f"{count} x {element} ({round(mass)} г/моль): {round(total_mass)} г/моль")
        except Exception as e:
            print(f"Ошибка: {e}")
            return redirect('/')
    return render_template('molyarnaya_massa.html', resultat=resultat, dlyproverki=dlyproverki, user=user, otdelno=otdelno)


def get_chemical_equation_solution(reaction):
    if request.method == 'POST':
        reaction = request.form.get("chemical_formula", False)
    # Кодируем реакцию для URL
        encoded_reaction = quote(reaction)

    # Формируем URL с учетом химической реакции
        url = f"https://chemequations.com/ru/?s={encoded_reaction}"

    # Отправляем GET-запрос
        response = requests.get(url)

    # Проверка успешности запроса
        if response.status_code == 200:
            # Парсим HTML-ответ
            soup = BeautifulSoup(response.text, 'html.parser')

            # Находим элемент с классом "equation main-equation well"
            result = soup.find('h1', class_='equation main-equation well')

            if result:
                return result.get_text(strip=True)
                # Возвращаем текст ответа
            else:
                return 'Решение не найдено.'
        else:
            return f"Ошибка при запросе: {response.status_code}"


@app.route('/complete_reaction', methods=['GET', 'POST'])
def complete_reaction_page():
    # страница, отвечающая за вывод завершенных реакций предыдущим методом
    react1 = ''
    user = flask_login.current_user
    reaction = ''
    if request.method == 'POST':
        reaction = request.form.get("chemical_formula", False)
        react1 = get_chemical_equation_solution(reaction)

    return render_template('complete_reaction.html', get_chemical_equation_solution=get_chemical_equation_solution, react1=react1, user=user, reaction=reaction)


def get_reaction_chain(reaction):
    # цепочка превращений
    if request.method == 'POST':
        reaction = request.form.get("chemical_formula", False)
        url = f"https://chemer.ru/services/reactions/chains/{reaction}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            content_sections = soup.find_all('section', class_='content')  # Ищем все секции с классом 'content'

            results = []  # Список для хранения первых ответов из каждой секции

            for content_section in content_sections:
                reactions = content_section.find_all('p', class_='resizable-block')  # Ищем все 'p' внутри каждой секции
                if reactions:
                    first_reaction = reactions[0].get_text().strip()  # Берем первый ответ из секции
                    results.append(first_reaction)  # Добавляем его в результаты

            return results  # Возвращаем список первых ответов из всех секций


@app.route('/get_reaction_chain', methods=['GET', 'POST'])
def get_reaction_chain_page():
    # страница, которая выводит цепочку превращений, т.е прошлую функцию
    user = flask_login.current_user
    react2 = ''
    reaction = ''
    if request.method == 'POST':
        reaction = request.form.get("chemical_formula", False)
        react2 = get_reaction_chain(reaction)

    return render_template('get_reaction_chain.html', get_reaction_chain=get_reaction_chain, user=user, reaction=reaction, react2=react2)


@app.route('/aboutme', methods=['GET', 'POST'])
def aboutme():
    # обо мне
    user = flask_login.current_user
    if user.is_authenticated:
        return render_template('about.html', user=user)
    else:
        return render_template('login.html', user=user)


@app.route('/instruction', methods=['GET', 'POST'])
def instruction():
    # инструкция
    user = flask_login.current_user
    return render_template('instruction.html', user=user)


@app.route('/documentation')
def documentation():
    user = flask_login.current_user
    return render_template('documentation.html', user=user)


chat_history_file = 'chat_history.json'


@app.route('/get_messages', methods=['GET'])
def get_messages():
    return jsonify(load_chat_history())


# Загрузка истории чата из файла
def load_chat_history():
    if os.path.exists(chat_history_file):
        with open(chat_history_file, 'r') as f:
            return json.load(f)  # Загружаем данные из JSON
    return []


# Сохранение сообщения в файл
def save_message(username, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    chat_entry = {
        'timestamp': timestamp,
        'username': username,
        'message': message
    }

    # Загружаем текущую историю чата
    chat_history = load_chat_history()
    chat_history.append(chat_entry)

    # Сохраняем обновленную историю в JSON-файл
    with open(chat_history_file, 'w') as f:
        json.dump(chat_history, f, indent=4)


def delete_all_messages():
    chat_history = load_chat_history()
    chat_history.clear()
    if chat_history != '':
        with open(chat_history_file, 'w') as f:
            json.dump(chat_history, f, indent=4)


# Удаление сообщения
def delete_message(index):
    chat_history = load_chat_history()
    if 0 <= index < len(chat_history):
        del chat_history[index]
        with open(chat_history_file, 'w') as f:
            json.dump(chat_history, f, indent=4)


chat = load_chat_history()  # Загружаем историю чата при старте


@app.route('/chat', methods=['GET', 'POST'])
def chat_messages():
    global chat
    user = flask_login.current_user
    if user.is_authenticated:
        if request.method == 'POST':
            if 'message' in request.form:  # Добавление сообщения
                s = request.form["message"]
                save_message(user.username, s)  # Сохраняем сообщение в файл
            elif 'delete' in request.form:  # Удаление сообщения
                index = int(request.form['delete'])
                if user.username == 'admin123' or chat[index]['username'] == user.username:
                    delete_message(index)  # Удаляем сообщение
            elif 'delete_all_messages' in request.form:
                if user.username == 'admin123':
                    delete_all_messages()
            chat = load_chat_history()  # Обновляем чат после сохранения/удаления
            return redirect(url_for('chat_messages'))  # Перенаправляем на ту же страницу
        return render_template('chat.html', user=user, chat=chat)
    else:
        return redirect(url_for('login'))


@app.route('/tablica', methods=['GET', 'POST'])
def tablica():
    # таблица менделеева
    user = flask_login.current_user
    return render_template('tablica.html', user=user)


@app.route('/tablica_rastvorimosti', methods=['GET', 'POST'])
def tablica_rastvorimosti():
    # таблица растворимости
    user = flask_login.current_user
    return render_template('tablica_rastvorimosti.html', user=user)


@app.route('/tablica_kislotnosti', methods=['GET', 'POST'])
def tablica_kislotnosti():
    # таблица кислот ( ошибка в названии функции ) :))
    user = flask_login.current_user
    return render_template('tablica_kislotnosti.html', user=user)


def minigamefunc():
    # функция обработчик миниигры
    a = random.randint(0, 117)
    atomic_masses = {
        'H': 'Водород',
        'He': 'Гелий',
        'Li': 'Литий',
        'Be': 'Бериллий',
        'B': 'Бор',
        'C': 'Углерод',
        'N': 'Азот',
        'O': 'Кислород',
        'F': 'Фтор',
        'Ne': 'Неон',
        'Na': 'Натрий',
        'Mg': 'Магний',
        'Al': 'Алюминий',
        'Si': 'Кремний',
        'P': 'Фосфор',
        'S': 'Сера',
        'Cl': 'Хлор',
        'Ar': 'Аргон',
        'K': 'Калий',
        'Ca': 'Кальций',
        'Sc': 'Скандий',
        'Ti': 'Титан',
        'V': 'Ванадий',
        'Cr': 'Хром',
        'Mn': 'Марганец',
        'Fe': 'Железо',
        'Co': 'Кобальт',
        'Ni': 'Никель',
        'Cu': 'Медь',
        'Zn': 'Цинк',
        'Ga': 'Галлий',
        'Ge': 'Германий',
        'As': 'Мышьяк',
        'Se': 'Селен',
        'Br': 'Бром',
        'Kr': 'Криптон',
        'Rb': 'Рубидий',
        'Sr': 'Стронций',
        'Y': 'Иттрий',
        'Zr': 'Цирконий',
        'Nb': 'Ниобий',
        'Mo': 'Молибден',
        'Tc': 'Технеций',
        'Ru': 'Рутений',
        'Rh': 'Родий',
        'Pd': 'Палладий',
        'Ag': 'Серебро',
        'Cd': 'Кадмий',
        'In': 'Индий',
        'Sn': 'Олово',
        'Sb': 'Сурьма',
        'Te': 'Теллур',
        'I': 'Йод',
        'Xe': 'Ксенон',
        'Cs': 'Цезий',
        'Ba': 'Барий',
        'La': 'Лантан',
        'Ce': 'Церий',
        'Pr': 'Празеодим',
        'Nd': 'Неодим',
        'Pm': 'Прометий',
        'Sm': 'Самарий',
        'Eu': 'Европий',
        'Gd': 'Гадолиний',
        'Tb': 'Тербий',
        'Dy': 'Диспрозий',
        'Ho': 'Гольмий',
        'Er': 'Эрбий',
        'Tm': 'Тулий',
        'Yb': 'Иттербий',
        'Lu': 'Лютеций',
        'Hf': 'Гафний',
        'Ta': 'Тантал',
        'W': 'Вольфрам',
        'Re': 'Рений',
        'Os': 'Осмий',
        'Ir': 'Иридий',
        'Pt': 'Платина',
        'Au': 'Золото',
        'Hg': 'Ртуть',
        'Tl': 'Таллий',
        'Pb': 'Свинец',
        'Bi': 'Висмут',
        'Po': 'Полоний',
        'At': 'Астат',
        'Rn': 'Радон',
        'Fr': 'Франций',
        'Ra': 'Радий',
        'Ac': 'Актиний',
        'Th': 'Торий',
        'Pa': 'Проактиний',
        'U': 'Уран',
        'Np': 'Нептуний',
        'Pu': 'Плутоний',
        'Am': 'Америций',
        'Cm': 'Кюрий',
        'Bk': 'Берклий',
        'Cf': 'Калифорний',
        'Es': 'Эйнштейний',
        'Fm': 'Фермий',
        'Md': 'Менделевий',
        'No': 'Нобелий',
        'Lr': 'Лоуренсий',
        'Rf': 'Резерфордий',
        'Db': 'Дубний',
        'Sg': 'Сиборгий',
        'Bh': 'Борий',
        'Hs': 'Хассий',
        'Mt': 'Майтнерий',
        'Ds': 'Дармштадтий',
        'Rg': 'Рентгений',
        'Cn': 'Коперниций',
        'Nh': 'Нихоний',
        'Fl': 'Флеровий',
        'Mc': 'Московий',
        'Lv': 'Ливерморий',
        'Ts': 'Теннессин',
        'Og': 'Оганессон',
    }
    k = []
    d = ''
    b = ""
    for i in atomic_masses:
        k.append(i)
    b = k[a]
    nazv = atomic_masses[b]
    print(b, nazv)
    return b, nazv


h = ['']
pravilno = 0
otvety = 0
@app.route('/minigame', methods=['GET', 'POST'])
def minigame():
    '''функция, которая возвращает страницу мини-игры
    Коротко о мини-игре:
    Это Игра для запоминания элементов таблицы Менделеева.
    Выводится элемент, а игрок должен написать, то как он называется на РУССКОМ языке'''
    d = ""
    global h, pravilno, otvety
    res = minigamefunc()
    b = res[0]
    nazv = res[1]
    user = flask_login.current_user
    h.append(nazv)
    if user.is_authenticated:
        if request.method == 'POST':
            element = request.form['element']
            print(h)
            if element == h[-2]:
                d = 'Верно, следующий'
                pravilno += 1
                user.pokupki = pravilno
                otvety += 1
                user.summa = otvety
                db.session.commit()
                if pravilno == 10:
                    right_percent = round((pravilno / otvety) * 100, 2)
                    pravilno = 0
                    otvety = 0
                    user.summa = otvety
                    user.pokupki = pravilno
                    db.session.commit()
                    h = ['']
                    return render_template('winning.html', user=user, right_percent=right_percent)
            else:
                d = f'Неправильно, ответ: {h[-2]}'
                otvety += 1
        return render_template('minigame.html', user=user, d=d, minigamefunc=minigamefunc, b=b, pravilno=pravilno, otvety=otvety)
    else:
        return redirect(url_for('login'))


def get_substance_html(substance_name):
    url = "https://chemer.ru/services/organic/structural"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')

        for row in rows:
            cols = row.find_all('td')
            if cols:
                name = cols[0].text.strip()
                link = cols[0].find('a')['href']
                if substance_name.lower() in name.lower():
                    substance_url = f"https://chemer.ru/services/organic/{link}"
                    substance_response = session.get(substance_url)
                    return substance_response.text
    return None


def extract_svg_and_symbols(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    svg_elements = soup.find_all('svg')
    symbols = soup.find_all('symbol')

    if not svg_elements:
        return None, None, None

    first_svg_content = str(svg_elements[0])
    if 'width' not in first_svg_content or 'height' not in first_svg_content:
        first_svg_content = first_svg_content.replace('<svg', '<svg width="200" height="200"')

    isomer_svgs = []
    spacing = 220  # Расстояние между изомерами
    max_per_row = 20  # Максимум изомеров в строке

    tab1_section = soup.find('section', id='tab1')

    # Найдем все таблицы в секции tab1
    tables = tab1_section.find_all('table')

    for table in tables:
        svg_elements2 = table.find_all('svg')

        for index, svg in enumerate(svg_elements2):
            row = index // max_per_row  # Определяем номер строки
            col = index % max_per_row  # Определяем номер колонки
            x = col * spacing  # Устанавливаем x координату
            y = row * 220  # Устанавливаем y координату для новой строки
            svg_str = str(svg).replace('<svg', f'<svg x="{x}" y="{y}"')  # Устанавливаем координаты
            isomer_svgs.append(svg_str)

    isomer_svgs_content = ''.join(isomer_svgs)
    symbol_content = ''.join(str(symbol) for symbol in symbols)

    return first_svg_content, isomer_svgs_content, symbol_content


@app.route('/orghim', methods=['GET', 'POST'])
def orghim():
    isomer_files = []
    user = flask_login.current_user
    if request.method == 'POST':
        substance_name = request.form['substance_name']
        html_code = get_substance_html(substance_name)

        if html_code:
            first_svg, isomers_svg, symbols_svg = extract_svg_and_symbols(html_code)

            # Сохраняем первую SVG-картинку и символы в файл
            if first_svg:
                with open('static/output.svg', 'w', encoding='utf-8') as f:
                    f.write(
                        f"<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>{symbols_svg}{first_svg}</svg>")

            # Сохраняем изомеры в отдельные файлы
            if isomers_svg.strip():
                isomer_files = []
                for index, svg in enumerate(isomers_svg.split('</svg>')):
                    if svg.strip():
                        file_name = f'static/isomer_{index}.svg'
                        with open(file_name, 'w', encoding='utf-8') as f:
                            f.write(f"<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>{svg}</svg>")
                        isomer_files.append(file_name)

            return render_template('orghim.html', svg_file='output.svg', isomer_files=isomer_files, substance_name=substance_name, user=user)

    return render_template('orghim.html', svg_file=None, isomer_files=None, user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # вход пользователя в аккаунт. берутся данные из базы данных
    user = flask_login.current_user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect('/')
        else:
            return render_template('bug.html', user=user)
    return render_template('login.html', user=user)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.request_loader
def load_user_from_request(request):
    user_id = request.args.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None


@app.route('/register', methods=['GET', 'POST'])
def register():
    # регистрация, идет работа с бд
    user = flask_login.current_user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        if not User.query.filter_by(username=username).first():
            user = User(username=username, name=name, surname=surname, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
        else:
            flash('Пользователь с таким именем уже существует.')
    return render_template('register.html', user=user)


@app.route('/profile')
def profile():
    # профиль
    user = flask_login.current_user
    if user.is_authenticated:
        return render_template('profile.html', user=user)
    else:
        return redirect(url_for('login'))


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    # изменить профиль
    user = flask_login.current_user
    if user.is_authenticated:
        if request.method == 'POST':
            username = request.form['username']
            name = request.form['name']
            surname = request.form['surname']
            email = request.form['email']

            user.username = username
            user.surname = surname
            user.name = name
            user.email = email
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            # Обработка загрузки аватара
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    user.avatar = filename  # Сохраняем имя файла в БД

            db.session.commit()
            flash('Ваш профиль обновлён успешно!', 'success')
            return redirect(url_for('profile'))

        return render_template('edit_profile.html', user=user)
    else:
        return redirect(url_for('login'))


with app.app_context():
    db.create_all()


@app.route('/logout')
@login_required
def logout():
    # выход из аккаунта
    flask_login.logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
