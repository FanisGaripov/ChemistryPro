from flask import Blueprint, jsonify, request
import g4f
from src.qualitative_reactions import qualitative_reactions_notorganic
from src.utils import (
    electronic_configuration,
    get_chemical_equation_solution,
    get_reaction_chain,
    molecular_mass,
    organic_reactions,
    uravnivanie,
)

"""API CHEMISTRYPRO"""


api = Blueprint("api", __name__)


@api.route("/get_reaction_chain/<q>", methods=["GET"])
def get_reaction_chain_api(q):
    answer = get_reaction_chain(q)
    return jsonify({"answer": " \n".join(answer)})


@api.route("/organic_reactions/<q>", methods=["GET"])
def organic_reactions_api(q):
    image_tags, dec_ans2 = organic_reactions(q)
    return jsonify(
        {"q": q.capitalize(), "image_tags": image_tags, "dec_ans2": dec_ans2}
    )


@api.route("/balancing_reactions/<q>", methods=["GET"])
def balancing_reactions_api(q):
    answer = uravnivanie(q)
    return jsonify({"answer": answer})


@api.route("/molyar_mass/<q>", methods=["GET"])
def molyar_mass_api(q):
    otdelno = ""
    massa, element_details = molecular_mass(q)
    resultat = f"Молярная масса {q}: {massa} г/моль"
    for element, mass, count, total_mass in element_details:
        otdelno += f"{count} x {element} ({round(mass, 2)} г/моль): {round(total_mass, 2)} г/моль, что составляет {round((round(total_mass, 2) / massa) * 100, 2)}%\n"
    return jsonify({"answer": resultat, "about_every_element": otdelno})


@api.route("/complete_reactions/<q>", methods=["GET"])
def complete_reactions_api(q):
    answer = get_chemical_equation_solution(q)
    if "(g)" in answer:
        answer = answer.replace("(g)", "")
    if "(s)" in answer:
        answer = answer.replace("(s)", "")
    if "(aq)" in answer:
        answer = answer.replace("(aq)", "")
    if "(l)" in answer:
        answer = answer.replace("(l)", "")
    qualitative = qualitative_reactions_notorganic(q)
    return jsonify({"answer": answer, "qualitative": qualitative})


@api.route("/electronic_confuguration/<q>", methods=["GET"])
def electronic_configuration_api(q):
    (
        configuration,
        school_configuration,
        graphic_representation,
        atomic_mass,
    ) = electronic_configuration(q)
    return jsonify(
        {
            "configuration": configuration,
            "school_configuration": school_configuration,
            "graphic_representation": graphic_representation,
            "atomic_mass": atomic_mass,
        }
    )


@api.route("/chatgpt", methods=["GET"])
def chatgpt_api():
    q = request.args.get("q")
    response = g4f.ChatCompletion.create(
        model="gpt-4", messages=[{"role": "user", "content": q}], stream=False
    )
    return jsonify({"response": response})
