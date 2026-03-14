import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import quote
import re
from chempy import balance_stoichiometry


def get_reaction_chain(reaction):
    # цепочка превращений
    if "=" in reaction and ">" not in reaction:
        reaction = reaction
        if " " in reaction:
            reaction = reaction.replace(" ", "")
    elif "-" in reaction and ">" not in reaction:
        reactions_list = reaction.split("-")
        reaction = ""
        for i in range(len(reactions_list)):
            if i != len(reactions_list) - 1:
                reaction += reactions_list[i] + "="
                if " " in reaction:
                    reaction = reaction.replace(" ", "")
            else:
                reaction += reactions_list[i]
                if " " in reaction:
                    reaction = reaction.replace(" ", "")
    elif (
        " " in reaction
        and ">" not in reaction
        and "=" not in reaction
        and "-" not in reaction
    ):
        reactions_list = reaction.split(" ")
        reaction = ""
        reactions_list = [r for r in reactions_list if r.strip() != ""]
        for i in range(len(reactions_list)):
            if i != len(reactions_list) - 1:
                reaction += reactions_list[i] + "="
                if " " in reaction:
                    reaction = reaction.replace(" ", "")
            else:
                reaction += reactions_list[i]
                if " " in reaction:
                    reaction = reaction.replace(" ", "")
    elif "->" in reaction:
        reactions_list = reaction.split("->")
        reaction = ""
        for i in range(len(reactions_list)):
            if i != len(reactions_list) - 1:
                reaction += reactions_list[i] + "="
                if " " in reaction:
                    reaction = reaction.replace(" ", "")
            else:
                reaction += reactions_list[i]
                if " " in reaction:
                    reaction = reaction.replace(" ", "")
    elif "=>" in reaction:
        reactions_list = reaction.split("=>")
        reaction = ""
        for i in range(len(reactions_list)):
            if i != len(reactions_list) - 1:
                reaction += reactions_list[i] + "="
                if " " in reaction:
                    reaction = reaction.replace(" ", "")
            else:
                reaction += reactions_list[i]
                if " " in reaction:
                    reaction = reaction.replace(" ", "")
    url = f"https://chemer.ru/services/reactions/chains/{reaction}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    session = requests.Session()
    session.headers.update(headers)
    response = session.get(url)

    if response.status_code == 200:
        final_results = []
        soup = BeautifulSoup(response.text, "html.parser")
        inset_divs = soup.find_all("div", class_="inset")  # Ищем все группы
        reaction_groups = {}  # Словарь для групп реакций

        # Сначала собираем группы из h2
        for inset_div in inset_divs:
            product_header = inset_div.find("h2")
            if product_header:
                product_text = product_header.get_text().strip()
                reaction_groups[product_text] = (
                    []
                )  # Создаем пустой список для реакций этой группы

        # Теперь собираем реакции и добавляем их в соответствующие группы
        content_sections = soup.find_all(
            "section", class_="content"
        )  # Ищем все секции с классом 'content'
        if content_sections:
            for content_section in content_sections:
                reactions = content_section.find_all(
                    "p", class_="resizable-block"
                )  # Ищем все 'p' внутри каждой секции
                if reactions:
                    # Находим соответствующую группу для текущей секции
                    group_header = content_section.find_previous(
                        "div", class_="inset"
                    ).find("h2")
                    if (
                        group_header
                        and group_header != "Все неизвестные вещества найдены"
                    ):
                        group_name = group_header.get_text().strip()
                        for reaction in reactions:
                            reaction_text = (
                                reaction.get_text().strip()
                            )  # Извлекаем текст реакции
                            if group_name in reaction_groups:
                                reaction_groups[group_name].append(
                                    reaction_text
                                )  # Добавляем реакцию в соответствующую группу
                else:
                    group_header = content_section.find_previous(
                        "div", class_="inset"
                    ).find("h2")
                    group_name = group_header.get_text().strip()
                    reactions = soup.find_all("a", rel="nofollow")
                    for reaction in reactions:
                        if group_name in reaction_groups:
                            reaction_groups[group_name].append(reaction.text)

        # Формируем окончательный результат
        for group, reactions in reaction_groups.items():
            if len(reactions) == 0:
                final_results.append(
                    "Реакция невозможна или ошибка в написании"
                )
                break
            elif group == "Все неизвестные вещества найдены":
                final_results.append(
                    f"{group}, попробуйте ввести эту реакцию уже с ниже приведенными веществами"
                )
                final_results.extend(reactions)
            else:
                final_results.append(f"Как из {group}:")
                final_results.extend(
                    reactions
                )  # Добавляем все реакции для данной группы

        return final_results  # Возвращаем сгруппированные реакции
    else:
        return [
            f"Ошибка при запросе: {response.status_code}"
        ]  # Обработка ошибки запроса
    return []


def organic_reactions(zapros):
    image_tags = []
    k = 0
    dec_ans2 = ""
    url = "http://acetyl.ru/process/recv.php"
    params = {"search": zapros, "sizesd": 1, "colsd": 0, "test": 0, "butt": 4}
    if zapros != "":
        response = requests.get(url, params=params)

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

        url2 = "http://acetyl.ru/klass/search.php"
        params2 = {"searvar": zapros}

        response = requests.get(url2, params=params2)
        if response.status_code == 200:
            answer = response.text
            parsed_data = json.loads(answer)
            res = parsed_data["res"]
            soup = BeautifulSoup(str(res), "html.parser")
            text_content = soup.get_text(separator="\n", strip=True)
            dec_ans2 = text_content
            dec_ans2 = dec_ans2[0::].split("\n")
            dec_ans2 = [item.capitalize() for item in dec_ans2 if item != ""]

    return image_tags, dec_ans2


def uravnivanie(formula):
    # баланс уравнений
    reactants_input, products_input = formula.split("=")
    reactants = {
        x.split()[0].strip(): int(x.split()[1]) if len(x.split()) > 1 else 1
        for x in reactants_input.split("+")
    }
    products = {
        x.split()[0].strip(): int(x.split()[1]) if len(x.split()) > 1 else 1
        for x in products_input.split("+")
    }

    balanced_reaction = balance_stoichiometry(reactants, products)

    reactants_str = " + ".join(
        [
            f"{v}{k}" if v != 1 else f"{k}"
            for k, v in balanced_reaction[0].items()
        ]
    )
    products_str = " + ".join(
        [
            f"{v}{k}" if v != 1 else f"{k}"
            for k, v in balanced_reaction[1].items()
        ]
    )

    otvet = f"{reactants_str} = {products_str}"

    return otvet


def molecular_mass(formula):
    # Словарь с атомными массами элементов
    atomic_masses = {
        "H": 1.008,
        "He": 4.0026,
        "Li": 6.94,
        "Be": 9.0122,
        "B": 10.81,
        "C": 12.011,
        "N": 14.007,
        "O": 15.999,
        "F": 18.998,
        "Ne": 20.180,
        "Na": 22.99,
        "Mg": 24.305,
        "Al": 26.982,
        "Si": 28.085,
        "P": 30.974,
        "S": 32.06,
        "Cl": 35.45,
        "Ar": 39.948,
        "K": 39.098,
        "Ca": 40.078,
        "Sc": 44.956,
        "Ti": 47.867,
        "V": 50.941,
        "Cr": 51.996,
        "Mn": 54.938,
        "Fe": 55.845,
        "Co": 58.933,
        "Ni": 58.693,
        "Cu": 63.546,
        "Zn": 65.38,
        "Ga": 69.723,
        "Ge": 72.630,
        "As": 74.922,
        "Se": 78.971,
        "Br": 79.904,
        "Kr": 83.798,
        "Rb": 85.468,
        "Sr": 87.62,
        "Y": 88.906,
        "Zr": 91.224,
        "Nb": 92.906,
        "Mo": 95.95,
        "Tc": 98,
        "Ru": 101.07,
        "Rh": 102.905,
        "Pd": 106.42,
        "Ag": 107.868,
        "Cd": 112.414,
        "In": 114.818,
        "Sn": 118.710,
        "Sb": 121.760,
        "Te": 127.60,
        "I": 126.904,
        "Xe": 131.293,
        "Cs": 132.905,
        "Ba": 137.327,
        "La": 138.905,
        "Ce": 140.116,
        "Pr": 140.907,
        "Nd": 144.242,
        "Pm": 145,
        "Sm": 150.36,
        "Eu": 151.964,
        "Gd": 157.25,
        "Tb": 158.925,
        "Dy": 162.500,
        "Ho": 164.930,
        "Er": 167.259,
        "Tm": 168.934,
        "Yb": 173.04,
        "Lu": 174.966,
        "Hf": 178.49,
        "Ta": 180.947,
        "W": 183.84,
        "Re": 186.207,
        "Os": 190.23,
        "Ir": 192.217,
        "Pt": 195.084,
        "Au": 196.967,
        "Hg": 200.592,
        "Tl": 204.38,
        "Pb": 207.2,
        "Bi": 208.980,
        "Po": 209,
        "At": 210,
        "Rn": 222,
        "Fr": 223,
        "Ra": 226,
        "Ac": 227,
        "Th": 232.038,
        "Pa": 231.035,
        "U": 238.028,
        "Np": 237,
        "Pu": 244,
        "Am": 243,
        "Cm": 247,
        "Bk": 247,
        "Cf": 251,
        "Es": 252,
        "Fm": 257,
        "Md": 258,
        "No": 259,
        "Lr": 262,
        "Rf": 267,
        "Db": 270,
        "Sg": 271,
        "Bh": 270,
        "Hs": 277,
        "Mt": 276,
        "Ds": 281,
        "Rg": 282,
        "Cn": 285,
        "Nh": 286,
        "Fl": 289,
        "Mc": 290,
        "Lv": 293,
        "Ts": 294,
        "Og": 294,
    }

    def parse_formula(formula):
        stack = []
        current = {}
        i = 0
        while i < len(formula):
            if formula[i] == "(" or formula[i] == "[":
                stack.append(current)
                current = {}
                i += 1
            elif formula[i] == ")" or formula[i] == "]":
                i += 1
                num = ""
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
                match = re.match(r"([A-Z][a-z]?)(\d*)", formula[i:])
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
        element_details.append(
            (element, atomic_masses[element], count, total_mass)
        )
        mass += total_mass

    return round(mass, 2), element_details


def get_chemical_equation_solution(reaction):
    """метод обработчик дописывания хим.реакций. коротко о нем: принимает
    из основной функции реакцию, вставляет ее в ссылку и возвращает ответ,
    который парсит(выкидывает все лишнее) только до нужных строчек
    """
    # Кодируем реакцию для URL
    encoded_reaction = quote(reaction)

    # Формируем URL с учетом химической реакции
    url = f"https://chemequations.com/ru/?s={encoded_reaction}"

    # Отправляем GET-запрос
    response = requests.get(url)

    # Проверка успешности запроса
    if response.status_code == 200:
        # Парсим HTML-ответ
        soup = BeautifulSoup(response.text, "html.parser")

        # Находим элемент с классом "equation main-equation well"
        result = soup.find("h1", class_="equation main-equation well")

        if result:
            return result.get_text(strip=True)
            # Возвращаем текст ответа
        else:
            return "Решение не найдено."
    else:
        return f"Ошибка при запросе: {response.status_code}"


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


def electronic_configuration(element):
    elements_data = {
        "H": 1,
        "He": 2,
        "Li": 3,
        "Be": 4,
        "B": 5,
        "C": 6,
        "N": 7,
        "O": 8,
        "F": 9,
        "Ne": 10,
        "Na": 11,
        "Mg": 12,
        "Al": 13,
        "Si": 14,
        "P": 15,
        "S": 16,
        "Cl": 17,
        "Ar": 18,
        "K": 19,
        "Ca": 20,
        "Sc": 21,
        "Ti": 22,
        "V": 23,
        "Cr": 24,
        "Mn": 25,
        "Fe": 26,
        "Co": 27,
        "Ni": 28,
        "Cu": 29,
        "Zn": 30,
        "Ga": 31,
        "Ge": 32,
        "As": 33,
        "Se": 34,
        "Br": 35,
        "Kr": 36,
        "Rb": 37,
        "Sr": 38,
        "Y": 39,
        "Zr": 40,
        "Nb": 41,
        "Mo": 42,
        "Tc": 43,
        "Ru": 44,
        "Rh": 45,
        "Pd": 46,
        "Ag": 47,
        "Cd": 48,
        "In": 49,
        "Sn": 50,
        "Sb": 51,
        "Te": 52,
        "I": 53,
        "Xe": 54,
        "Cs": 55,
        "Ba": 56,
        "La": 57,
        "Ce": 58,
        "Pr": 59,
        "Nd": 60,
        "Pm": 61,
        "Sm": 62,
        "Eu": 63,
        "Gd": 64,
        "Tb": 65,
        "Dy": 66,
        "Ho": 67,
        "Er": 68,
        "Tm": 69,
        "Yb": 70,
        "Lu": 71,
        "Hf": 72,
        "Ta": 73,
        "W": 74,
        "Re": 75,
        "Os": 76,
        "Ir": 77,
        "Pt": 78,
        "Au": 79,
        "Hg": 80,
        "Tl": 81,
        "Pb": 82,
        "Bi": 83,
        "Po": 84,
        "At": 85,
        "Rn": 86,
        "Fr": 87,
        "Ra": 88,
        "Ac": 89,
        "Th": 90,
        "Pa": 91,
        "U": 92,
        "Np": 93,
        "Pu": 94,
        "Am": 95,
        "Cm": 96,
        "Bk": 97,
        "Cf": 98,
        "Es": 99,
        "Fm": 100,
        "Md": 101,
        "No": 102,
        "Lr": 103,
        "Rf": 104,
        "Db": 105,
        "Sg": 106,
        "Bh": 107,
        "Hs": 108,
        "Mt": 109,
        "Ds": 110,
        "Rg": 111,
        "Cn": 112,
        "Nh": 113,
        "Fl": 114,
        "Mc": 115,
        "Lv": 116,
        "Ts": 117,
        "Og": 118,
    }

    atomic_number = elements_data.get(element)
    atomic_number1 = elements_data.get(element)
    atom = atomic_number
    if element == "":
        return "Введите элемент", ""
    if atomic_number is None:
        return "Элемент не найден", ""

    configurations = []
    subshells = [
        "1s",
        "2s",
        "2p",
        "3s",
        "3p",
        "4s",
        "3d",
        "4p",
        "5s",
        "4d",
        "5p",
        "6s",
        "4f",
        "5d",
        "6p",
        "7s",
        "5f",
        "6d",
        "7p",
    ]
    electrons = [2, 2, 6, 2, 6, 2, 10, 6, 2, 10, 6, 2, 14, 10, 6, 2, 14, 10, 6]

    for i in range(len(subshells)):
        if atomic_number > 0:
            if atomic_number >= electrons[i]:
                configurations.append(f"{subshells[i]}^{electrons[i]}")
                atomic_number -= electrons[i]
            else:
                configurations.append(f"{subshells[i]}^{atomic_number}")
                break

    configurations1 = configurations

    priority = {
        "1s": 1,
        "2s": 2,
        "2p": 3,
        "3s": 4,
        "3p": 5,
        "3d": 6,
        "4s": 7,
        "4p": 8,
        "4d": 9,
        "4f": 10,
        "5s": 11,
        "5p": 12,
        "5d": 13,
        "5f": 14,
        "6s": 15,
        "6p": 16,
        "6d": 17,
        "7s": 18,
        "7p": 19,
    }

    configurations2 = sorted(
        configurations1,
        key=lambda x: priority.get(x.split("^")[0], float("inf")),
    )

    configuration_string = " ".join(configurations)
    configuration_string2 = " ".join(configurations2)

    # Графическое представление(текстовое, используются [↑] и [↓], открывающая и закрывающая скобка - это одна клетка)
    graphic_representation = generate_graphical_representation(configurations)

    return (
        configuration_string,
        configuration_string2,
        graphic_representation,
        atom,
    )