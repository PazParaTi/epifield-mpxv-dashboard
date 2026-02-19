# aggregator.py
from parsers import (
    parse_demographics, parse_inclusion_exclusion, parse_symptoms, parse_evolution_maladie,
    parse_expositions, parse_comorbidites, parse_vaccination, parse_signs_vitaux,
    parse_etat_general, parse_lesions, parse_ganglions, parse_examen_neuro,
    parse_orl_yeux, parse_thoracique_card, parse_abdominal, parse_genital,
    parse_pcr, parse_sample_collection, parse_lab_processing, parse_suivi
)

def parse_document(full_text):
    data = {}

    data.update(parse_demographics(full_text))
    data.update(parse_inclusion_exclusion(full_text))
    data.update(parse_symptoms(full_text))
    data.update(parse_evolution_maladie(full_text))
    data.update(parse_expositions(full_text))
    data.update(parse_comorbidites(full_text))
    data.update(parse_vaccination(full_text))
    data.update(parse_signs_vitaux(full_text))
    data.update(parse_etat_general(full_text))
    data.update(parse_lesions(full_text))
    data.update(parse_ganglions(full_text))
    data.update(parse_examen_neuro(full_text))
    data.update(parse_orl_yeux(full_text))
    data.update(parse_thoracique_card(full_text))
    data.update(parse_abdominal(full_text))
    data.update(parse_genital(full_text))
    data.update(parse_pcr(full_text, "lésionnaire"))
    data.update(parse_pcr(full_text, "oropharyngé"))
    data.update(parse_sample_collection(full_text))
    # Ajouter pour chaque type lab: data.update(parse_lab_processing(full_text, "SST")) etc.
    for jour in ["J4", "J8", "J14", "J28", "J56"]:
        data.update(parse_suivi(full_text, jour))
    
    return data

def aggregate_all_docs(documents_dict):
    """
    documents_dict : { filename: full_text }
    Retourne une liste d'objets avec toutes les variables detectées.
    """
    rows = []
    for fname, text in documents_dict.items():
        row = parse_document(text)
        row["source_file"] = fname
        rows.append(row)
    return rows