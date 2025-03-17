def qualitative_reactions_notorganic(reaction):
    # Переделка таблицы с умскула: https://kasheloff.ru/photos/kakaya-para-ionov/36
    # таблица качественных реакций в неорганических реакциях
    reactant_list = [reactant.strip() for reactant in reaction.split('+')]

    def are_ions_in_different_substances(ion1, ion2):
        ion1_found = False
        ion2_found = False
        for substance in reactant_list:
            if ion1 == substance:
                ion1_found = True
            if ion2 == substance:
                ion2_found = True
            if ion1 in substance and ion2 in substance:
                ion1_found = False
                ion2_found = False
        rez = ion1_found and ion2_found
        return rez

    if are_ions_in_different_substances('Ba', 'SO4'):
        return 'Белый осадок'
    if are_ions_in_different_substances('NH4', 'OH'):
        return 'Запах аммиака'
    if are_ions_in_different_substances('Ca', 'CO2') or are_ions_in_different_substances('Ca', 'SO4'):
        return 'Белый осадок'
    if are_ions_in_different_substances('Mg', 'OH'):
        return 'Белый осадок'
    if are_ions_in_different_substances('Al', 'OH'):
        return 'Белый осадок, растворим в избытке щелочи'
    if are_ions_in_different_substances('Zn', 'OH'):
        return 'Белый осадок, растворим в избытке щелочи'
    if are_ions_in_different_substances('Cr', 'OH'):
        return 'Серо-зеленый осадок, растворим в избытке щелочи'
    if are_ions_in_different_substances('Fe', 'OH'):
        return 'Если заряд Fe(2+), то Серо-зелёный осадок, растворим в избытке щелочи. Если Fe(3+), то темно-бурый осадок'
    if are_ions_in_different_substances('Cu', 'OH') or are_ions_in_different_substances('Cu', 'S'):
        return 'Голубой осадок'
    if are_ions_in_different_substances('Ag', 'Cl2'):
        return 'Белый осадок'
    if are_ions_in_different_substances('Br2', 'Ag'):
        return 'Светло-жёлтый осадок'
    if are_ions_in_different_substances('I2', 'Ag'):
        return 'Жёлтый осадок'
    if are_ions_in_different_substances('S', 'H'):
        return 'Запах тухлых яиц'
    if are_ions_in_different_substances('S', 'Cu') or are_ions_in_different_substances('S', 'Pb') or are_ions_in_different_substances('S', 'Ag'):
        return 'Чёрный осадок'
    if are_ions_in_different_substances('S', 'Mn'):
        return 'Розовый осадок'
    if are_ions_in_different_substances('SO4', 'Ba') or are_ions_in_different_substances('SO4', 'Ag'):
        return 'Белый осадок'
    if are_ions_in_different_substances('PO4', 'Ag'):
        return 'Жёлтый осадок'
    if are_ions_in_different_substances('PO4', 'Ca'):
        return 'Белый осадок'
    if are_ions_in_different_substances('CO3', 'H'):
        return 'Выделение газа'
    if are_ions_in_different_substances('SiO3', 'H'):
        return 'Белый студенистый осадок'
    if are_ions_in_different_substances('Pb', 'I2'):
        return 'Образование ярко-желтого осадка'
    if are_ions_in_different_substances('Ca', 'F2'):
        return 'Белый осадок'
    if are_ions_in_different_substances('SO3', 'H'):
        return 'Выделение газа с сильным запахом'
    if are_ions_in_different_substances('CO3', 'Ca'):
        return 'Белый осадок'
    if are_ions_in_different_substances('CrO4', 'Ba'):
        return 'Желтый осадок'

    return 'Качественная реакция не обнаружена'