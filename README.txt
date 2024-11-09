Eng:
Introduction
ChemistryPro is a web application designed for studying Chemistry at the school level of grades 8-11. It offers users various functions for interacting with chemical element data.

A little bit about the architecture of this site: The site is based on the Python programming language. Python has a large number of libraries, which is an advantage of this programming language. Flask is the main library on which this site is based.

pip install flask
The Flask framework is a universal solution for many sites, and it is also easy to learn. The HTML files of the project are stored in the templates folder, and the images in the static folder. Project structure:

ChemistryPro/
├── static/                # Static files such as CSS and images
│ ├── /upload # Avatars
│   └── fon.jpg...                      # Other photos
├── templates/             # HTML Templates
about.html # About me
│ ├─── base.html # Basic Template
│ ├─── bug.html # In case of errors
│ ├─── complete_reaction.html # Adding reactions
│ ├─── documentation.html # Documentation
│ ├─── electronic_configuration.html # Electronic configuration
│ ├─── get_reaction_chain.html # Chains of transformations
│ ├─── index.html # Equalizing reactions
│ ├─── instruction.html # Instructions
│ ├─── login.html # Login
│ ├─── main.html # Main page
of the site minigame.html # MiniGame
│ ├─── molyarnaya_massa.html # Molar masses
│ ├─── orghim.html # The structure of the org. in-in
│   ├── profile.html # Profiles
│ ├─── register.html # Registration
│ ├─── tablica.html # The Periodic Table
│ ├─── tablica_kislotnosti.html # Acidity table
│ ├─── tablica_rastvorimosti.html # Solubility table
│ └─── winning.html # Winning a MiniGame
├── server.py # Main application file
├─── mod.py # All models for the user database are stored here
└─── requirements.txt # List of dependencies (libraries)
            
The source code of the program is open, the program can be found at the link:

https://github.com/FanisGaripov/ChemistyPro
Functions
1. Adding chemical reactions
This function allows, in the presence of known reaction reagents, to obtain a reaction product. It works by sending a request to the server chemequations.com . The requests library (python) is used.

 pip install requests
def get_chemical_equation_solution(reaction):
    if request.method == 'POST':
        reaction = request.form.get("chemical_formula", False)
    # Encoding the reaction for the URL
        encoded_reaction = quote(reaction)

    # We form the URL taking into account the chemical reaction
        url = f"https://chemequations.com/ru/?s={encoded_reaction}"

    # Sending a GET request
        response = requests.get(url)...
2. Equalization of chemical reactions
This function allows you to equalize any chemical reaction. The chempy library(python) is used.

pip install chempy
It works using the built-in method of the chempy library, namely balance_stoichiometry.
def uravnivanie(formula):
    ...# balance of equations
balanced_reaction = balance_stoichiometry(reactants, products)
reactants_str = '+'.join([f"{v}{k}" for k, v in balanced_reaction[0].items()])
products_str = '+'.join([f"{v}{k}" for k, v in balanced_reaction[1].items()])
otvet = f"{reactants_str} = {products_str}"...
3. Electronic configuration
This function allows you to find out the electronic configuration of any substance without looking at the periodic table. It does not use any other libraries except flask (python, the main library on which the entire project is based). The simplest function to implement.

def electronic_configuration(element):

    ...for i in range(len(subshells)):
        if atomic_number > 0:
            if atomic_number >= electrons[i]:
                configurations.append(f"{subshells[i]}^{electrons[i]}")
                atomic_number -= electrons[i]
            else:
                configurations.append(f"{subshells[i]}^{atomic_number}")
                break
    return ' '.join(configurations)...
            
4. Molar mass of substances
The function allows you to find out the molar reaction of any substance or reaction. The data on the mass of the element is taken from the periodic table, then this mass is multiplied by the coefficient of the element. You can get the entire mass as a whole, as well as the mass of each element individually.

        try:
            dlyproverki, element_details = molecular_mass(chemical_formula)
            resultat = f"Molar mass {chemical_formula}: {dlyproverki} g/mol"
            for element, mass, count, total_mass in element_details:
                otdelno.append(f"{count} x {element} ({round(mass)} g/mol): {round(total_mass)} g")
            
5. Chains of transformations
The function allows you to find out the whole chain of transformations of a substance, namely what reactions must occur to obtain a particular substance. It works by sending a request to the server chemer.ru . The implementation will require the requests library(python). We send a request to the server, and it should return the html of all reactions to us. It is extremely important to enter substances in the field. Since the data from the field is entered in the url of the site, it is important that this data is formatted. The main requirement when entering: enter all reactions through the "=" sign. For example: Al=Al2O3=AlCl3=Al(OH)3=Na3AlO3=Al(NO3)3.

def get_reaction_chain(reaction):
    # chain of transformations
if request.method == 'POST':
reaction = request.form.get("chemical_formula", False)
url = f"https://chemer.ru/services/reactions/chains /{reaction}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            content_sections = soup.find_all('section', class_='content') # We are looking for all sections with the 'content' class...
            
6. The structure of organic reactions
The function allows you to find an organic substance, namely its graphical representation. For example: when you enter 2,2-dimethylbutane, pictures in .svg format should be displayed. The first such picture will be the substance itself, and the second larger picture will be all the isomers of the substance (or those that represent the resource to which we send the request). All this is implemented using the requests library (python), i.e. we also send a request to the site and it returns a response to us. Despite such a seemingly simple implementation, the code of this part was the most difficult to write. Here is a part of it:


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
        rows = table.find_all('tr')...

def extract_svg_and_symbols(html_code):
    soup = BeautifulSoup(html_code, 'html.parser')
    svg_elements = soup.find_all('svg')
    symbols = soup.find_all('symbol')

    if not svg_elements:
        return None, None, None

    first_svg_content = str(svg_elements[0])
    if 'width' not in first_svg_content or 'height' not in first_svg_content:
        first_svg_content = first_svg_content.replace()...

@app.route('/orghim', methods=['GET', 'POST'])
def orghim():
    user = flask_login.current_user
    if request.method == 'POST':
        substance_name = request.form['substance_name']
        html_code = get_substance_html(substance_name)

        if html_code:
            first_svg, isomers_svg, symbols_svg = extract_svg_and_symbols(html_code)...
            
Tables
1. The Periodic Table
The page returns the periodic table. How does it work? A PSCE table has been downloaded from Internet resources, which is displayed on the page. Also, by scrolling through the page below, you can see details about each element.

2.Solubility table
The page returns a solubility table.

3.Table of acids and acid residues
The page returns acids and their residues, and there is also a table of acid strengths: from the weakest to the strongest.

The code for all these pages is similar, I'll show you only one:


@app.route('/tablica', methods=['GET', 'POST'])
def tablica():
# periodic table
    user = flask_login.current_user
    return render_template('tablica.html', user=user)
            
Also, of course, you need to create an html file with a page before writing it into your code.

General chat
The general chat is intended for communication between users of the site. Here you can search for new friends, find a solution to your problem, and just share your findings. A prerequisite for using the chat: authorization on the site.

A mini-game
The mini-game is designed to train memory on chemical elements. The game starts showing random elements from the periodic table, and the player must guess what it is called.

How to play:
Enter the name of the item in Russian.
If the answer is correct, the following element will be displayed.
The game continues until 10 correct answers are reached.
If the player gets more than 50% of the correct answers, then he wins. Otherwise, it's a loss.

Contacts:
garipovfanis1@yandex.ru




Rus:
Введение
ChemistryPro — это веб-приложение, разработанное для изучения Химии школьного уровня 8-11 классов. Оно предлагает пользователям различные функции для взаимодействия с данными о химических элементах.

Немного об архитектуре этого сайта: Сайт основан на языке программирования Python. Python обладает большим количеством библиотек, что является преимуществом этого языка программирования. Flask - это основная библиотека на которой базируется этот сайт.

pip install flask
Фреймворк Flask является универсальным решением для многих сайтов, а также он легок в изучении. Html-файлы проекта хранятся в папке templates, а изображения в папке static. Структура проекта:

ChemistryPro/
├── static/                # Статические файлы, такие как CSS и изображения
│   ├── /upload                         # Аватары
│   └── fon.jpg...                      # Остальные фото
├── templates/             # Шаблоны HTML
│   ├── about.html                      # Обо мне
│   ├── base.html                       # Базовый шаблон
│   ├── all_profiles.html               # Список всех пользователей сайта
│   ├── bug.html                        # В случае ошибок
│   ├── chat.html                       # Чат
│   ├── complete_reaction.html          # Дописывание реакций
│   ├── documentation.html              # Документация
│   ├── edit_profile.html               # Редактирование профиля
│   ├── electronic_configuration.html   # Электронная конфигурация
│   ├── get_reaction_chain.html         # Цепочки превращений
│   ├── index.html                      # Уравнивание реакций
│   ├── instruction.html                # Инструкция
│   ├── login.html                      # Логин
│   ├── main.html                       # Главная страница
│   ├── minigame.html                   # МиниИгра
│   ├── molyarnaya_massa.html           # Молярные массы
│   ├── orghim.html                     # Структура орг. в-в
│   ├── otherprofile.html               # Профиля пользователей (для пользователя, который просматривает другие профили)
│   ├── profile.html                    # Профили
│   ├── register.html                   # Регистрация
│   ├── tablica.html                    # Таблица Менделеева
│   ├── tablica_kislotnosti.html        # Таблица кислотностей
│   ├── tablica_rastvorimosti.html      # Таблица растворимостей
│   └── winning.html                    # Победа в МиниИгре
├── server.py              # Главный файл приложения
├── mod.py                 # Здесь хранятся все модели для базы данных пользователей
└── requirements.txt       # Список зависимостей(библиотек)
            
Исходный код программы открытый, программу можно найти по ссылке:

https://github.com/FanisGaripov/ChemistyPro
Функции
1. Дописывание химических реакций
Это функция позволяет, при наличии известных реагентов реакции, получить продукт реакции. Работает при помощи отправки запроса на сервер chemequations.com . Используется библиотека requests(python).

2. Уравнивание химических реакций
Эта функция позволяет уравнять любую химическую реакцию. Используется библиотека chempy(python).
Работает при помощи встроенного метода библиотеки chempy, а именно balance_stoichiometry.

3. Электронная конфигурация
Эта функция позволяет узнать электронную конфигурацию любого вещества без заглядывания в таблицу Менделеева. Не использует других библиотек, кроме flask(python, основная библиотека, на которой держится весь проект). Самая простая функция в реализации.
          
4. Молярная масса веществ
Функция позволяет узнать молярную реакцию любого вещества или реакции. Данные о массе элемента берутся из таблицы Менделеева, далее эта масса умножается на коэффициент элемента. Можно получить всю массу целиком, а также массу каждого элемента по отдельности.
            
5. Цепочки превращений
Функция позволяет узнать целую цепочку превращений вещества, а именно какие реакции должны произойти, чтобы получить то или иное вещество. Работает при помощи отправки запроса на сервер chemer.ru . Для реализации потребуется библиотека requests(python). Мы отправляем запрос на сервер, а тот должен нам вернуть html всех реакций. Крайне важен ввод веществ в поле. Т.к данные из поля вводятся в url сайта, то важно чтобы эти данные были отформатированы. Главное требование при вводе: все реакции вводить через знак "=". Например: Al=Al2O3=AlCl3=Al(OH)3=Na3AlO3=Al(NO3)3.
            
6. Структура органических реакций
Функция позволяет найти органическое вещество, а именно его графическое представление. Например: при вводе 2,2-диметилбутан, должны вывестись картинки в формате .svg. Первой такой картинкой будет само вещество, а вторая картинка побольше - все изомеры вещества(или те, что представляет ресурс, на который мы отправляем запрос). Все это реализовано при помощи библиотеки requests(python), т.е мы также отправляем запрос на сайт и он возвращает нам ответ. Несмотря на такую, казалось бы простую реализацию, код этой часть был самым трудным в написании. Вот его часть:
            
Таблицы
1.Таблица Менделеева
Страница возвращает таблицу Менделеева. Как она работает? Из интернет-ресурсов была скачана таблица ПСХЭ, которая отображается на странице. Также пролистнув страницу ниже можно увидеть подробности про каждый элемент.

2.Таблица растворимости
Страница возвращает таблицу растворимостей.

3.Таблица кислот и кислотных остатков
Страница возвращает кислоты и их остатки, также есть таблица сил кислот: от самой слабой, до самой сильной.

Общий чат
Общий чат предназначен для общения пользователей сайта. Здесь Вы можете искать новых друзей, найти решение своей проблемы, а также просто поделиться своими находками. Обязательное условие пользования чатом: авторизация на сайте.

Мини-игра
Мини-игра предназначена для тренировки памяти по химическим элементам. Игра начинает показывать случайные элементы из таблицы Менделеева, а игрок должен угадать как он называется.
Как играть:
Введите название элемента на русском языке.
Если ответ верный, будет показан следующий элемент.
Игра продолжается до достижения 10 правильных ответов.
Если игрок набирает больше 50% правильных ответов, то он выигрывает. Иначе-проигрыш.

Контакты:
garipovfanis1@yandex.ru
