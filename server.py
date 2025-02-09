from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify, send_file, send_from_directory
import re
from mod import db, User, UserGameState
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
from dotenv import load_dotenv
# импортируем все библиотеки

app = Flask(__name__)
load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/upload'
app.secret_key = 'supersecretkey'
login_manager = LoginManager()
login_manager.init_app(app)
db.init_app(app)
c = []


def download_avatar_from_yandex_disk(filename):
    token = os.getenv('YANDEX_TOKEN')
    headers = {
        'Authorization': f'OAuth {token}'
    }

    # Получение ссылки для загрузки
    download_url = f'https://cloud-api.yandex.net/v1/disk/resources/download?path=users_avatars/{filename}'
    response = requests.get(download_url, headers=headers)

    if response.status_code == 200:
        download_link = response.json().get('href')

        # Проверяем, получена ли ссылка на загрузку
        if not download_link:
            print(f'No download link received for {filename}.')
            return False

        # Загрузка файла
        avatar_response = requests.get(download_link)

        if avatar_response.status_code == 200:
            with open(os.path.join('static/upload', filename), 'wb') as f:
                f.write(avatar_response.content)
            return True
        else:
            print(f'Failed to download the file. Status code: {avatar_response.status_code}')
            print(f'Response content: {avatar_response.content}')
    else:
        print(f'Failed to get download URL. Status code: {response.status_code}')
        print(f'Response content: {response.content}')

    return False

def check_and_download_avatars():
    users = User.query.all()
    for user in users:
        if user.avatar:
            avatar_path = os.path.join('static/upload', user.avatar)
            if not os.path.exists(avatar_path):
                print(f'Avatar for user {user.username} not found, downloading from Yandex Disk...')
                if download_avatar_from_yandex_disk(user.avatar):
                    print(f'Avatar for user {user.username} downloaded successfully.')
                else:
                    print(f'Failed to download avatar for user {user.username}.')
        else:
            print(f'User {user.username} has no avatar defined.')


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

    def parse_formula(formula):
        stack = []
        current = {}
        i = 0
        while i < len(formula):
            if formula[i] == '(' or formula[i] == '[':
                stack.append(current)
                current = {}
                i += 1
            elif formula[i] == ')' or formula[i] == ']':
                i += 1
                num = ''
                while i < len(formula) and formula[i].isdigit():
                    num += formula[i]
                    i += 1
                multiplier = int(num) if num else 1
                for element, count in current.items():
                    current[element] = count * multiplier
                if stack:
                    parent = stack.pop()
                    for element, count in current.items():
                        if element in parent:
                            parent[element] += count
                        else:
                            parent[element] = count
                    current = parent
            else:
                match = re.match(r'([A-Z][a-z]?)(\d*)', formula[i:])
                if match:
                    element, count = match.groups()
                    count = int(count) if count else 1
                    if element in current:
                        current[element] += count
                    else:
                        current[element] = count
                    i += len(match.group(0))
                else:
                    i += 1
        return current

    element_counts = parse_formula(formula)
    mass = 0.0
    element_details = []
    for element, count in element_counts.items():
        element_mass = atomic_masses[element]
        total_mass = element_mass * count
        element_details.append((element, atomic_masses[element], count, total_mass))
        mass += total_mass

    return round(mass, 2), element_details


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
    atomic_number1 = elements_data.get(element)
    atom = atomic_number
    if element == '':
        return "Введите элемент", ""
    if atomic_number is None:
        return "Элемент не найден", ""

    configurations = []
    configurations1 = []
    subshells = ['1s', '2s', '2p', '3s', '3p', '4s', '3d', '4p', '5s', '4d', '5p', '6s', '4f', '5d', '6p', '7s', '5f',
                 '6d', '7p']
    electrons = [2, 2, 6, 2, 6, 2, 10, 6, 2, 10, 6, 2, 14, 10, 6, 2, 14, 10, 6]

    subshells1 = ['1s', '2s', '2p', '3s', '3p', '3d', '4s', '4p', '4d', '4f', '5s', '5p', '5d', '5f', '6s', '6p', '6d',
                  '7s', '7p']
    electrons1 = [2, 2, 6, 2, 6, 10, 2, 6, 10, 14, 2, 6, 10, 14, 2, 6, 10, 2, 6]

    for i in range(len(subshells)):
        if atomic_number > 0:
            if atomic_number >= electrons[i]:
                configurations.append(f"{subshells[i]}^{electrons[i]}")
                atomic_number -= electrons[i]
            else:
                configurations.append(f"{subshells[i]}^{atomic_number}")
                break

    for i in range(len(subshells1)):
        if atomic_number1 > 0:
            if atomic_number1 >= electrons1[i]:
                configurations1.append(f"{subshells1[i]}^{electrons1[i]}")
                atomic_number1 -= electrons1[i]
            else:
                configurations1.append(f"{subshells1[i]}^{atomic_number1}")
                break

    configuration_string = ' '.join(configurations)

    configuration_string2 = ' '.join(configurations1)

    # Графическое представление(текстовое, используются [↑] и [↓], открывающая и закрывающая скобка - это одна клетка)
    graphic_representation = generate_graphical_representation(configurations)

    return configuration_string, configuration_string2, graphic_representation, atom


def generate_graphical_representation(configurations):
    # графическое представление электронной конфигурации
    representation = []
    grouped_representation = {}

    for config in configurations:
        subshell, count = config.split('^')
        count = int(count)

        if subshell[0] not in grouped_representation:
            grouped_representation[subshell[0]] = []

        cells = []

        if subshell.endswith('s'):
            for _ in range(1):
                if count > 0:
                    cells.append('[↑]')
                    count -= 1
                if count > 0:
                    cells[0] += '[↓]'
                    count -= 1
                else:
                    cells.append('[ ]')  # Пустая ячейка

        elif subshell.endswith('p'):
            # 3 p-орбитали
            for i in range(3):
                if count > 0:
                    cells.append('[↑]')
                    count -= 1
                else:
                    cells.append('[ ]')  # Пустая ячейка

            for i in range(3):
                if count > 0:
                    cells[i] += '[↓]'
                    count -= 1

        elif subshell.endswith('d'):
            # 5 d-орбиталей
            for i in range(5):
                if count > 0:
                    cells.append('[↑]')
                    count -= 1
                else:
                    cells.append('[ ]')  # Пустая ячейка

            for i in range(5):
                if count > 0:
                    cells[i] += '[↓]'
                    count -= 1

        elif subshell.endswith('f'):
            # 7 f-орбиталей
            for i in range(7):
                if count > 0:
                    cells.append('[↑]')
                    count -= 1
                else:
                    cells.append('[ ]')  # Пустая ячейка

            for i in range(7):
                if count > 0:
                    cells[i] += '[↓]'
                    count -= 1

        grouped_representation[subshell[0]].append(f"{subshell}: " + ' '.join(cells))

    # Сборка финального представления
    for level in sorted(grouped_representation.keys()):
        representation.extend(grouped_representation[level])

    return "\n".join(representation)


@app.route('/electronic_configuration', methods=['GET', 'POST'])
def electronic_configuration_page():
    # функция, которая отображает страницу электронной конфигурации, предыдущая функция отвечает за обработку ответа
    element = ''
    user = flask_login.current_user
    configuration = ''
    configuration1 = ''
    graphic_representation = ''
    atomic = ''
    if request.method == 'POST':
        element = request.form.get("element", False)
        try:
            configuration, configuration1, graphic_representation, atomic = electronic_configuration(element)
        except Exception as e:
            configuration1, configuration, graphic_representation, atomic = '', '', '', ''
    return render_template('electronic_configuration.html', configuration=configuration, configuration1=configuration1, graphic_representation=graphic_representation, atomic=atomic, user=user, element=element)


def uravnivanie(formula):
    # баланс уравнений
    reactants_input, products_input = formula.split('=')
    reactants = {x.split()[0].strip(): int(x.split()[1]) if len(x.split()) > 1 else 1 for x in
                 reactants_input.split('+')}
    products = {x.split()[0].strip(): int(x.split()[1]) if len(x.split()) > 1 else 1 for x in products_input.split('+')}

    balanced_reaction = balance_stoichiometry(reactants, products)

    reactants_str = ' + '.join([f"{v}{k}" if v != 1 else f"{k}" for k, v in balanced_reaction[0].items()])
    products_str = ' + '.join([f"{v}{k}" if v != 1 else f"{k}" for k, v in balanced_reaction[1].items()])

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
                otdelno.append(f"{count} x {element} ({round(mass, 2)} г/моль): {round(total_mass, 2)} г/моль, что составляет {round((round(total_mass, 2) / dlyproverki) * 100, 2)}%")
        except Exception as e:
            otdelno.append(f"{e}: такого вещества или соединения не существует")
    return render_template('molyarnaya_massa.html', resultat=resultat, dlyproverki=dlyproverki, user=user, otdelno=otdelno)


def get_chemical_equation_solution(reaction):
    '''метод обработчик дописывания хим.реакций. коротко о нем: принимает из основной функции реакцию, вставляет
    ее в ссылку и возвращает ответ, который парсит(выкидывает все лишнее) только до нужных строчек'''
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
        if '(g)' in react1:
            react1 = react1.replace('(g)', '')
        if '(s)' in react1:
            react1 = react1.replace('(s)', '')
        if '(aq)' in react1:
            react1 = react1.replace('(aq)', '')
        if '(l)' in react1:
            react1 = react1.replace('(l)', '')

    return render_template('complete_reaction.html', get_chemical_equation_solution=get_chemical_equation_solution, react1=react1, user=user, reaction=reaction)


def get_reaction_chain(reaction):
    # цепочка превращений
    if request.method == 'POST':
        if '=' in reaction and '>' not in reaction:
            reaction = reaction
        elif '-' in reaction and '>' not in reaction:
            reactions_list = reaction.split('-')
            reaction = ''
            for i in range(len(reactions_list)):
                if i != len(reactions_list) - 1:
                    reaction += reactions_list[i] + '='
                else:
                    reaction += reactions_list[i]
        elif ' ' in reaction:
            reactions_list = reaction.split(' ')
            reaction = ''
            for i in range(len(reactions_list)):
                if i != len(reactions_list) - 1:
                    reaction += reactions_list[i] + '='
                else:
                    reaction += reactions_list[i]
        elif '->' in reaction:
            reactions_list = reaction.split('->')
            reaction = ''
            for i in range(len(reactions_list)):
                if i != len(reactions_list) - 1:
                    reaction += reactions_list[i] + '='
                else:
                    reaction += reactions_list[i]
        elif '=>' in reaction:
            reactions_list = reaction.split('=>')
            reaction = ''
            for i in range(len(reactions_list)):
                if i != len(reactions_list) - 1:
                    reaction += reactions_list[i] + '='
                else:
                    reaction += reactions_list[i]
        url = f"https://chemer.ru/services/reactions/chains/{reaction}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url)

        if response.status_code == 200:
            final_results = []
            soup = BeautifulSoup(response.text, 'html.parser')
            inset_divs = soup.find_all('div', class_='inset')  # Ищем все группы
            reaction_groups = {}  # Словарь для групп реакций

            # Сначала собираем группы из h2
            for inset_div in inset_divs:
                product_header = inset_div.find('h2')
                if product_header:
                    product_text = product_header.get_text().strip()
                    reaction_groups[product_text] = []  # Создаем пустой список для реакций этой группы

            # Теперь собираем реакции и добавляем их в соответствующие группы
            content_sections = soup.find_all('section', class_='content')  # Ищем все секции с классом 'content'
            if content_sections:
                for content_section in content_sections:
                    reactions = content_section.find_all('p', class_='resizable-block')  # Ищем все 'p' внутри каждой секции
                    if reactions:
                        # Находим соответствующую группу для текущей секции
                        group_header = content_section.find_previous('div', class_='inset').find('h2')
                        if group_header and group_header != 'Все неизвестные вещества найдены':
                            group_name = group_header.get_text().strip()
                            for reaction in reactions:
                                reaction_text = reaction.get_text().strip()  # Извлекаем текст реакции
                                if group_name in reaction_groups:
                                    reaction_groups[group_name].append(reaction_text)  # Добавляем реакцию в соответствующую группу
                    else:
                        group_header = content_section.find_previous('div', class_='inset').find('h2')
                        group_name = group_header.get_text().strip()
                        reactions = soup.find_all('a', rel='nofollow')
                        for reaction in reactions:
                            if group_name in reaction_groups:
                                reaction_groups[group_name].append(reaction.text)

            # Формируем окончательный результат
            for group, reactions in reaction_groups.items():
                if len(reactions) == 0:
                    final_results.append('Реакция невозможна или ошибка в написании')
                    break
                elif group == 'Все неизвестные вещества найдены':
                    final_results.append(f'{group}, попробуйте ввести эту реакцию уже с ниже приведенными веществами')
                    final_results.extend(reactions)
                else:
                    final_results.append(f"Как из {group}:")
                    final_results.extend(reactions)  # Добавляем все реакции для данной группы

            return final_results  # Возвращаем сгруппированные реакции
        else:
            return [f"Ошибка при запросе: {response.status_code}"]  # Обработка ошибки запроса
    return []


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


@app.route('/rastvory', methods=['GET', 'POST'])
def rastvory():
    # калькулятор растворимостей
    user = flask_login.current_user
    if request.method == 'POST':
        # Получаем данные из формы
        mass_solution = request.form.get('mass_solution', type=float)  # Масса раствора (г)
        mass_solute = request.form.get('mass_solute', type=float)      # Масса растворенного вещества (г)
        mass_fraction = request.form.get('mass_fraction', type=float)  # Массовая доля (в %)

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

        return render_template('rastvory.html', mass_solution=mass_solution, mass_solute=mass_solute, mass_fraction=mass_fraction, user=user)

    return render_template('rastvory.html', user=user)


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
    polzovatel = User.query.filter_by(username=username).first()
    avatarka = polzovatel.avatar
    chat_entry = {
        'timestamp': timestamp,
        'avatar': avatarka,
        'username': username,
        'message': message
    }

    # Загружаем текущую историю чата
    chat_history = load_chat_history()
    chat_history.append(chat_entry)

    # Сохраняем обновленную историю в JSON-файл
    with open(chat_history_file, 'w') as f:
        json.dump(chat_history, f, indent=4)


# Удаление всех сообщений разом(доступно только администраторам)
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
    # чат
    global chat
    user = flask_login.current_user
    if user.is_authenticated:
        if request.method == 'POST':
            if 'message' in request.form:  # Добавление сообщения
                s = request.form["message"]
                save_message(user.username, s)  # Сохраняем сообщение в файл
            elif 'delete' in request.form:  # Удаление сообщения
                index = int(request.form['delete'])
                if user.admin == 1 or chat[index]['username'] == user.username:
                    delete_message(index)  # Удаляем сообщение
            elif 'delete_all_messages' in request.form:
                if user.admin == 1:
                    delete_all_messages()
            chat = load_chat_history()  # Обновляем чат после сохранения/удаления
            return redirect(url_for('chat_messages'))  # Перенаправляем на ту же страницу
        return render_template('chat.html', user=user, chat=chat)
    else:
        return redirect(url_for('login'))


@app.route('/chat/saving')
def chat_saving():
    # Загрузка истории чата
    if chat_history_file != '[]':
        file_path = os.path.join('chat_history.json')
        return send_file(file_path, as_attachment=True)
    else:
        return 'Чат пуст'


@app.route('/download-db')
def download_db():
    # загрузка базы данных пользователя. вынужден использовать, т.к не могу встроить миграцию на хостинг
    user = flask_login.current_user
    if user.is_authenticated and user.admin == 1:
        try:
            return send_from_directory(
                directory='instance',  # Папка, где хранится база данных
                path='products.db',  # Имя файла базы данных
                as_attachment=True  # Это указывает, что файл должен быть скачан
            )
        except Exception as e:
            return str(e), 404
    else:
        bugcode = 6
        return render_template('bug.html', bugcode=bugcode, user=user)


@app.route('/tablica', methods=['GET', 'POST'])
def tablica():
    # таблица менделеева
    user = flask_login.current_user
    return render_template('tablica.html', user=user)


@app.route('/sw.js')
def sw():
    return app.send_static_file('sw.js')


@app.route('/yandex_682e07bf768831de.html')
def ya():
    user = flask_login.current_user
    return render_template('yandex_682e07bf768831de.html', user=user)


@app.route('/googled5c4e477b332cb57.html')
def google():
    user = flask_login.current_user
    return render_template('googled5c4e477b332cb57.html', user=user)


@app.route('/offline.html')
def offline():
    return app.send_static_file('offline.html')


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


@app.route('/sw.js')
def service_worker():
    return send_from_directory(app.static_folder, 'sw.js')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(app.static_folder, 'manifest.json')


@app.route('/uchebnik', methods=['GET', 'POST'])
def uchebnik():
    # я не знаю почему учебник, но это просто страница со справочным материалом по органике
    user = flask_login.current_user
    return render_template('uchebnik.html', user=user)


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
    return b, nazv


@app.route('/minigame', methods=['GET', 'POST'])
def minigame():
    # функция, которая возвращает страницу мини-игры
    d = ""
    user = flask_login.current_user

    # Получаем или создаём состояние игры для пользователя
    if user.is_authenticated:
        game_state = UserGameState.query.filter_by(user_id=user.username).first()

        if not game_state:
            game_state = UserGameState(user_id=user.username, answer_list='')  # Инициализируем список
            db.session.add(game_state)
            db.session.commit()

        res = minigamefunc()
        b = res[0]
        nazv = res[1]

        # Добавляем название элемента в answer_list
        game_state.answer_list = str(game_state.answer_list)
        game_state.answer_list += (f' {nazv}')

        # Сохраняем изменения после добавления
        db.session.commit()

        # Повторное извлечение состояния игры
        game_state = UserGameState.query.filter_by(user_id=user.username).first()

        if user.is_authenticated and user.username == game_state.user_id:
            if request.method == 'POST':
                element = request.form['element']

                if element.capitalize() == game_state.answer_list.split()[-2]:
                    d = 'Верно, следующий'
                    user.pokupki += 1
                    user.summa += 1
                    game_state.correct_answers = user.pokupki
                    game_state.total_answers = user.summa
                    db.session.commit()

                    if game_state.total_answers >= 10 and user.pokupki >= 10:
                        right_percent = round((game_state.correct_answers / game_state.total_answers) * 100, 2)
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
                        game_state.answer_list = ''  # Здесь мы обнуляем answer_list
                        db.session.commit()  # Сохраняем изменения
                        return render_template('winning.html', user=user, right_percent=right_percent)
                else:
                    d = f'Неправильно, ответ: {game_state.answer_list.split()[-2]}'
                    game_state.total_answers += 1
                    user.summa += 1
                    db.session.commit()

            return render_template('minigame.html', user=user, d=d, minigamefunc=minigamefunc, b=b,
                                   pravilno=game_state.correct_answers, otvety=game_state.total_answers)

    else:
        return redirect(url_for('login'))


@app.route('/reset_minigame', methods=['GET', 'POST'])
def reset_minigame():
    # сброс статистики миниигры. добавляется +1 к игре и сбрасывается вся статистика
    user = flask_login.current_user
    game_state = UserGameState.query.filter_by(user_id=user.username).first()
    if user.username == game_state.user_id:
        user.allgames += 1
        game_state.answer_list = ''
        game_state.total_answers = 0
        game_state.correct_answers = 0
        user.summa = 0
        user.pokupki = 0
        db.session.commit()
        return redirect(url_for('minigame'))
    else:
        bugcode = 9
        return render_template('bug.html', user=user, bugcode=bugcode)


def get_substance_html(substance_name):
    # получение имени орг вещества из таблицы на сайте при помощи парсинга этой страницы
    url = "https://chemer.ru/services/organic/structural"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url)
    global klass
    klass = ''
    namez = []

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr')

        for row in rows:
            cols = row.find_all('td')
            if cols:
                name = cols[0].text.strip()
                klass = cols[1].text.strip()
                link = cols[0].find('a')['href']
                if substance_name.lower() in name.lower() and substance_name.lower() == name.lower():
                    substance_url = f"https://chemer.ru/services/organic/{link}"
                    substance_response = session.get(substance_url)
                    return substance_response.text, None
                elif substance_name.lower() in name.lower() and name.lower()[2:] != substance_name.lower():
                    namez.append(name)
                elif substance_name.lower() in name.lower() and name.lower()[:2] == 'н-' and name.lower()[2:] == substance_name.lower():
                    substance_url = f"https://chemer.ru/services/organic/{link}"
                    substance_response = session.get(substance_url)
                    return substance_response.text, None
    return None, namez


def extract_svg_and_symbols(html_code):
    # занимается сохранением свг-картинок на сервер
    soup = BeautifulSoup(html_code, 'html.parser')
    svg_elements = soup.find_all('svg')
    symbols = soup.find_all('symbol')
    names = ''

    if not svg_elements:
        return None, None, None

    first_svg_content = str(svg_elements[0])
    if 'width' not in first_svg_content or 'height' not in first_svg_content:
        first_svg_content = first_svg_content.replace('<svg', '<svg width="200" height="200"')

    isomer_svgs = []
    spacing = 220  # Расстояние между изомерами
    max_per_row = 20  # Максимум изомеров в строке

    # Извлечение секции с id='tab1'
    tab1_section = soup.find('section', id='tab1')

    if tab1_section:
        # Получаем все SVG элементы внутри секции
        svg_elements2 = tab1_section.find_all('svg')
        names = tab1_section.find_all('a')

        for index, svg in enumerate(svg_elements2):
            row = index // max_per_row  # Определяем номер строки
            col = index % max_per_row  # Определяем номер колонки
            x = col - 1  # Устанавливаем x координату
            y = row  # Устанавливаем y координату для новой строки
            svg_str = str(svg).replace('<svg', f'<svg x="{x}" y="{y}"')  # Устанавливаем координаты
            isomer_svgs.append(svg_str)

    isomer_svgs_content = ''.join(isomer_svgs)
    symbol_content = ''.join(str(symbol) for symbol in symbols)

    return first_svg_content, isomer_svgs_content, symbol_content, names


@app.route('/orghim', methods=['GET', 'POST'])
def orghim():
    # основная страница для работы с методами(предыдущими двумя). Все вместе это ф-ция орг.химии
    # ее суть в выведении названий веществ и картинок изомеров и самого вещества
    # изомеров только 10, т.к 70 изомеров декана, например, может сильно нагрузить устройство пользователя и сервер,
    # который может обрабатывать несколько таких запросов, что приведет к замедлению его работы(он и так бесплатный)
    global klass
    combined = ''
    isomer_files = []
    variants = ''
    user = flask_login.current_user
    substance_name = ''
    if request.method == 'POST':
        substance_name = request.form['substance_name']
        html_code, variants = get_substance_html(substance_name)

        if html_code:
            first_svg, isomers_svg, symbols_svg, names = extract_svg_and_symbols(html_code)

            # Сохраняем первую SVG-картинку и символы в файл
            if first_svg:
                with open('static/output.svg', 'w', encoding='utf-8') as f:
                    f.write(
                        f"<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>{symbols_svg}{first_svg}</svg>")

            # Сохраняем изомеры в отдельные файлы
            if isomers_svg.strip():
                isomer_files = []
                nazvaniya = []
                for index, svg in enumerate(isomers_svg.split('</svg>')):
                    if index <= 9:
                        if svg.strip():
                            file_name = f'static/isomer_{index}.svg'
                            with open(file_name, 'w', encoding='utf-8') as f:
                                f.write(f"<svg xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink'>Х{symbols_svg}{svg}</svg></svg>")
                            filename_without_static = f'isomer_{index}.svg'
                            isomer_files.append(filename_without_static)

                for i, nazv in enumerate(names):
                    if i <= 9:
                        soup = BeautifulSoup(str(nazv), 'html.parser')
                        nazv = soup.a.text
                        nazvaniya.append(nazv.capitalize())
                combined = list(zip(nazvaniya, isomer_files))

            return render_template('orghim.html', svg_file='output.svg', isomer_files=isomer_files, substance_name=substance_name, user=user, klass=klass, combined=combined)

    return render_template('orghim.html', svg_file=None, isomer_files=None, nazvaniya=None, user=user, variants=variants, substance_name=substance_name)


@app.errorhandler(404)
def page_not_found(e):
    # просто обработчик ошибок, нужен, чтобы говорить пользователю, что такой страницы нет
    user = flask_login.current_user
    bugcode = 6
    return render_template('bug.html', user=user, bugcode=bugcode), 404


bugcode = 0
@app.route('/login', methods=['GET', 'POST'])
def login():
    bugcode = 0
    # вход пользователя в аккаунт. берутся данные из базы данных
    user = flask_login.current_user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect('/')
        elif not User.query.filter_by(username=username).first():
            bugcode = 1
            return render_template('bug.html', bugcode=bugcode, user=user)
        else:
            bugcode = 2
            user = ""
            return render_template('bug.html', bugcode=bugcode, user=user)
    if user.is_authenticated:
        return redirect(url_for('profile'))
    else:
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
    bugcode = 0
    # регистрация, идет работа с бд
    user = flask_login.current_user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        if not User.query.filter_by(username=username).first():
            if password == confirm_password:
                user = User(username=username, name=name, surname=surname, email=email)
                user.set_password(password)
                try:
                    db.session.add(user)
                    db.session.commit()
                    return redirect(url_for('login'))
                except:
                    bugcode = 4
                    return render_template('bug.html', bugcode=bugcode, user=user)
            else:
                bugcode = 5
                return render_template('bug.html', bugcode=bugcode, user=user)
        elif User.query.filter_by(username=username).first():
            bugcode = 3
            return render_template('bug.html', bugcode=bugcode, user=user)
        else:
            bugcode = 4
            return render_template('bug.html', bugcode=bugcode, user=user)
    return render_template('register.html', user=user)


@app.route('/profile')
def profile():
    # профиль
    user = flask_login.current_user
    if user.is_authenticated:
        return render_template('profile.html', user=user)
    else:
        return redirect(url_for('login'))


@app.route('/delete_account/<username>', methods=['GET', 'POST'])
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
                if filename != 'default_avatar.png':
                    avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    if os.path.exists(avatar_path):
                        os.remove(avatar_path)
            except:
                bugcode = 8
                return render_template('bug.html', user=user, bugcode=bugcode)
            if user.admin == 1:
                return redirect(url_for('all_profiles'))
            else:
                return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


@app.route('/profile/<username>', methods=["POST", "GET"])
def other_profiles(username):
    # профили других людей
    polzovatel = User.query.filter_by(username=username).first()
    user = flask_login.current_user

    if polzovatel:
        admin = polzovatel.admin
        if polzovatel != user:
            return render_template('otherprofile.html', user=user, polzovatel=polzovatel, admin=admin)
        else:
            return render_template('profile.html', user=user)
    else:
        bugcode = 7
        return render_template("bug.html", user=user, bugcode=bugcode)


@app.route('/profile/<username>/make_admin', methods=['GET', 'POST'])
def make_admin(username):
    # возможность одного админа присвоить админку другому. удалению возможно только вручную через бд
    polzovatel = User.query.filter_by(username=username).first()
    user = flask_login.current_user
    admin = polzovatel.admin
    if user.admin == 1:
        polzovatel.admin = 1
        db.session.commit()
        return render_template('otherprofile.html', user=user, polzovatel=polzovatel, admin=admin)
    else:
        bugcode = 6
        return render_template('bug.html', user=user, bugcode=bugcode)


@app.route('/all_profiles/', methods=['GET', 'POST'])
def all_profiles():
    # функция, которая выводит список всех пользователей сайта
    user = flask_login.current_user
    polzovatel = User.query.all()
    return render_template('all_profiles.html', user=user, polzovatel=polzovatel)


# Функция загрузки файла на Яндекс.Диск
def upload_to_yandex_disk(file_path, filename):
    # Источник доступа к API
    token = os.getenv('YANDEX_TOKEN')
    headers = {
        'Authorization': f'OAuth {token}'
    }
    # URL для загрузки файла
    upload_url = f'https://cloud-api.yandex.net/v1/disk/resources/upload?path=users_avatars/{filename}&overwrite=true'
    response = requests.get(upload_url, headers=headers)

    if response.status_code == 200:
        upload_link = response.json().get('href')
        with open(file_path, 'rb') as f:
            requests.put(upload_link, data=f)
        return True
    return False


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = flask_login.current_user

    if request.method == 'POST':
        # Получение данных из формы
        username = request.form['username']
        name = request.form['name']
        surname = request.form['surname']
        email = request.form['email']
        status = request.form['status']
        checking = User.query.filter_by(username=username).first()

        if checking and checking.id != user.id:
            bugcode = 4
            return render_template('bug.html', user=user, bugcode=bugcode)

        user.username = username
        user.name = name
        user.surname = surname
        user.email = email
        user.status = status

        # Загрузка аватара
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)  # Локальное сохранение файла на сервер

                # Загружаем файл на Yandex.Disk
                if upload_to_yandex_disk(file_path, filename):
                    user.avatar = filename  # Сохраняем имя файла в БД

        try:
            db.session.commit()
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for('edit_profile'))

    return render_template('edit_profile.html', user=user)


with app.app_context():
    db.create_all()
    check_and_download_avatars()


@app.route('/logout')
@login_required
def logout():
    # выход из аккаунта
    flask_login.logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
