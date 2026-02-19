# parsers.py
import re

# --- OUTIL : extraction générique par regex ---
def extract_with_regex(text, pattern, default=None, group=1):
    m = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
    return m.group(group).strip() if m else default

def extract_bool(text, pattern):
    return bool(re.search(pattern, text, re.IGNORECASE | re.UNICODE))

def extract_list(text, items, pattern_template=r"{item}.*?0\s*Oui"):
    result = {}
    for item in items:
        key = item.lower().replace(' ', '_').replace('é', 'e').replace('è', 'e').replace('ê', 'e')
        pattern = pattern_template.format(item=item)
        result[key] = extract_bool(text, pattern)
    return result

# --- PATTERNS AMÉLIORÉS ET ÉTENDUS ---

def parse_demographics(text):
    return {
        "age": extract_with_regex(text, r"(Âge|Age)[\s:]+(\d+)"),
        "date_naissance": extract_with_regex(text, r"Date de naissance.*?(\d{2}/\w{3}/\d{4})"),
        "sexe": extract_with_regex(text, r"Sexe[\s:]*([HF])"),
        "residence_deplacement_recent": extract_with_regex(text, r"Résidence / déplacement récent\s*:\s*(.+?)(?:\n|$)"),
        "sejour_zone_touchee": extract_bool(text, r"Séjour dans zone touchée.*?0\s*Oui"),
    }

def parse_inclusion_exclusion(text):
    inclusion_prosp = ["var1", "var2", "var3"]  # Remplacer par noms réels si connus
    inclusion_retro = ["var1", "var2", "var3", "var4"]
    exclusion_prosp = ["var1"]
    exclusion_retro = ["var1", "var2"]
    
    result = {}
    result.update({f"inclusion_prosp_{i+1}": extract_bool(text, f"Inclusion prospective.*?variable {i+1}.*?0\s*Oui") for i in range(3)})
    result.update({f"inclusion_retro_{i+1}": extract_bool(text, f"Inclusion rétrospective.*?variable {i+1}.*?0\s*Oui") for i in range(4)})
    result.update({f"exclusion_prosp_{i+1}": extract_bool(text, f"Exclusion prospective.*?variable {i+1}.*?0\s*Oui") for i in range(1)})
    result.update({f"exclusion_retro_{i+1}": extract_bool(text, f"Exclusion rétroprospective.*?variable {i+1}.*?0\s*Oui") for i in range(2)})
    return result

def parse_symptoms(text):
    symptoms_list = [
        "Asymptomatique", "Fièvre", "Lésions cutanées", "Symptômes grippaux", "Maux de tête",
        "Rougeur des yeux", "Écoulement oculaire", "Maux de gorge", "Toux", "Douleur thoracique",
        "Douleur abdominale", "Diarrhée", "Nausée", "Vomissements", "Miction douloureuse"
    ]
    result = {}
    for sym in symptoms_list:
        key = sym.lower().replace(' ', '_').replace('é', 'e').replace('è', 'e')
        result[f"{key}_present"] = extract_bool(text, f"{sym}.*?Symptôme présent.*?0\s*Oui")
        result[f"{key}_encore_present"] = extract_bool(text, f"{sym}.*?Symptôme encore présent.*?0\s*Oui")
    result["autres_symptomes"] = extract_with_regex(text, r"Autres symptômes décrits\s*:\s*(.+?)(?:\n|$)") or ""
    return result

def parse_evolution_maladie(text):
    return {
        "date_premiers_symptomes": extract_with_regex(text, r"Date des premiers symptômes.*?(\d{2}/\w{3}/\d{4})"),
        "patient_sous_traitement_mpxv": extract_bool(text, r"Patient sous traitement MPXV.*?0\s*Oui"),
        "type_traitement_tecovirimat": extract_bool(text, r"Type de traitement.*?Técovirimat.*?0\s*Oui"),
        "type_traitement_brincidofovir": extract_bool(text, r"Type de traitement.*?Brincidofovir.*?0\s*Oui"),
        "type_traitement_autres": extract_with_regex(text, r"Autres \(texte\)\s*:\s*(.+?)(?:\n|$)"),
        "date_debut_traitement": extract_with_regex(text, r"Date de début de traitement.*?(\d{2}/\w{3}/\d{4})"),
    }

def parse_expositions(text):
    return {
        "antecedent_voyage": extract_bool(text, r"Antécédent de voyage.*?0\s*Oui"),
        "voyage_zone_epidemie": extract_bool(text, r"Voyage en zone d’épidémie.*?0\s*Oui"),
        "pays_visite": extract_with_regex(text, r"Pays visité\s*:\s*(.+?)(?:\n|$)"),
        "district_province": extract_with_regex(text, r"District/province\s*:\s*(.+?)(?:\n|$)"),
        "contact_cas_confirm_suspect": extract_bool(text, r"Contact avec cas confirmé ou suspect.*?0\s*Oui"),
        "autres_expositions": extract_with_regex(text, r"Autres expositions significatives\s*:\s*(.+?)(?:\n|$)") or "",
    }

def parse_comorbidites(text):
    return {
        "vih_charge_supprimee": extract_bool(text, r"VIH.*?charge supprimée.*?0\s*Oui"),
        "vih_non_supprimee": extract_bool(text, r"VIH.*?non supprimée.*?0\s*Oui"),
        "vih_sans_arv": extract_bool(text, r"VIH.*?sans ARV.*?0\s*Oui"),
        "malnutrition_severe": extract_bool(text, r"Malnutrition sévère.*?0\s*Oui"),
        "ist": extract_bool(text, r"IST.*?0\s*Oui"),
        "tumeur_maligne": extract_bool(text, r"Tumeur maligne.*?0\s*Oui"),
        "autres_maladies_chroniques": extract_with_regex(text, r"Autres maladies chroniques\s*:\s*(.+?)(?:\n|$)") or "",
    }

def parse_vaccination(text):
    return {
        "vaccin_variole": extract_bool(text, r"Vaccin variole.*?0\s*Oui"),
        "vaccin_varicelle": extract_bool(text, r"Vaccin varicelle.*?0\s*Oui"),
        "vaccin_mva": extract_bool(text, r"Vaccin MVA.*?0\s*Oui"),
        "autres_vaccins": extract_with_regex(text, r"Autres vaccins\s*:\s*(.+?)(?:\n|$)") or "",
    }

def parse_signs_vitaux(text):
    return {
        "temperature": extract_with_regex(text, r"Température[\s:]+(\d+\.?\d*)"),
        "tension_arterielle": extract_with_regex(text, r"Tension artérielle[\s:]+(\d+/\d+)"),
        "frequence_respiratoire": extract_with_regex(text, r"Fréquence respiratoire[\s:]+(\d+)"),
        "frequence_cardiaque": extract_with_regex(text, r"Fréquence cardiaque[\s:]+(\d+)"),
        "poids": extract_with_regex(text, r"Poids[\s:]+(\d+\.?\d*)"),
        "taille": extract_with_regex(text, r"Taille[\s:]+(\d+\.?\d*)"),
    }

def parse_etat_general(text):
    return {
        "etat_general": extract_with_regex(text, r"État général[\s:]+(Très malade|Modérément|Légèrement|Normal)"),
    }

def parse_lesions(text):
    types = ["macules", "papules", "vésicules", "pustules", "ulcérations", "croûtes", "cicatrices", "lésions hémorragiques", "surinfection", "autre"]
    localisations = ["tête/visage/cou", "bras", "jambes", "tronc", "bouche", "paumes", "plantes", "conjonctive", "organes génitaux externes", "périnée", "canal vaginal", "rectum", "autres"]
    
    result = {}
    result["types_lesions"] = ";".join([t for t in types if extract_bool(text, f"Type.*?{t}.*?0\s*Oui")])
    result["localisations"] = ";".join([l for l in localisations if extract_bool(text, f"Localisation.*?{l}.*?0\s*Oui")])
    result["localisation_majoritaire"] = extract_with_regex(text, r"Localisation majoritaire\s*:\s*(.+?)(?:\n|$)") or ""
    result["description_lesion_prelevee"] = extract_with_regex(text, r"Description de la lésion prélevée\s*:\s*(.+?)(?:\n|$)") or ""
    return result
    return result

def parse_ganglions(text):
    localisations = ["cervical", "axillaire", "inguinal", "autre"]  # Assumer 4 choix
    natures = ["discret", "enchevêtré", "tendre", "caoutchouteux"]
    
    result = {
        "presence_adenopathies": extract_with_regex(text, r"Présence d’adénopathies[\s:]+(Oui|Non|NA)"),
        "localisations_ganglions": ";".join([l for l in localisations if extract_bool(text, f"Localisation.*?{l}.*?0\s*Oui")]),
        "taille_ganglions_mm": extract_with_regex(text, r"Taille \(mm\)[\s:]+(\d+)"),
        "nature_ganglions": ";".join([n for n in natures if extract_bool(text, f"Nature.*?{n}.*?0\s*Oui")]),
        "sensibilite_ganglions": extract_with_regex(text, r"Sensibilité[\s:]+(Oui|Non|NA)"),
        "autres_constatations_ganglions": extract_with_regex(text, r"Autres constatations\s*:\s*(.+?)(?:\n|$)") or "",
    }
    return result

def parse_examen_neuro(text):
    return {
        "examen_neuro": extract_with_regex(text, r"Examen neurologique[\s:]+(Normal|Non|NA)"),
        "signes_meninges": extract_bool(text, r"Si non.*?Signes méningés.*?0\s*Oui"),
        "deficits_focaux": extract_bool(text, r"Si non.*?Déficits focaux.*?0\s*Oui"),
        "autres_neuro": extract_with_regex(text, r"Autres[\s:]+(.+?)(?:\n|$)") or "",
    }

def parse_orl_yeux(text):
    return {
        "examen_orl_yeux": extract_with_regex(text, r"ORL / yeux[\s:]+(Normal|Non)"),
        "conjonctivite": extract_bool(text, r"Sinon.*?conjonctivite.*?0\s*Oui"),
        "lesions_corneennes": extract_bool(text, r"Sinon.*?lésions cornéennes.*?0\s*Oui"),
        "otite": extract_bool(text, r"Sinon.*?otite.*?0\s*Oui"),
        "mastoidite": extract_bool(text, r"Sinon.*?mastoïdite.*?0\s*Oui"),
        "pharyngite": extract_bool(text, r"Sinon.*?pharyngite.*?0\s*Oui"),
        "autres_orl": extract_with_regex(text, r"autres[\s:]+(.+?)(?:\n|$)") or "",
    }

def parse_thoracique_card(text):
    vars = ["tachypnée", "dyspnée", "sibilants", "râles", "murmures", "tachycardie", "bradycardie", "pouls faible"]
    return extract_list(text, vars, pattern_template=r"{item}.*?0\s*Oui")

def parse_abdominal(text):
    vars = ["distension", "sensibilité", "hépatomégalie", "splénomégalie", "ascite", "autres"]
    result = extract_list(text, vars[:-1], pattern_template=r"{item}.*?0\s*Oui")
    result["autres_abdominal"] = extract_with_regex(text, r"autres[\s:]+(.+?)(?:\n|$)") or ""
    return result

def parse_genital(text):
    vars = ["sensibilité sus-pubienne", "adénopathies inguinales", "vessie distendue", "lésions pénis", "lésions périnéales", "autres"]
    result = extract_list(text, vars[:-1], pattern_template=r"{item}.*?0\s*Oui")
    result["autres_genital"] = extract_with_regex(text, r"autres[\s:]+(.+?)(?:\n|$)") or ""
    return result

def parse_pcr(text, type_ecouv="lésionnaire"):
    prefix = "écouvillon lésionnaire" if type_ecouv == "lésionnaire" else "oropharyngé"
    return {
        f"pcr_{type_ecouv}_date": extract_with_regex(text, rf"{prefix}.*?Date test.*?(\d{{2}}/\w{{3}}/\d{{4}})"),
        f"pcr_{type_ecouv}_test_utilise": extract_with_regex(text, rf"{prefix}.*?Test utilisé\s*:\s*(.+?)(?:\n|$)"),
        f"pcr_{type_ecouv}_lot": extract_with_regex(text, rf"{prefix}.*?Lot\s*:\s*(\S+)"),
        f"pcr_{type_ecouv}_expiration": extract_with_regex(text, rf"{prefix}.*?Date d’expiration.*?(\d{{2}}/\w{{3}}/\d{{4}})"),
        f"pcr_{type_ecouv}_run_pass": extract_with_regex(text, rf"{prefix}.*?Run pass[\s:]+(Oui|No)"),
        f"pcr_{type_ecouv}_resultat": extract_with_regex(text, rf"{prefix}.*?Résultat[\s:]+(Détecté|Non détecté|Inconclusif|Invalide)"),
        f"pcr_{type_ecouv}_ct_value": extract_with_regex(text, rf"{prefix}.*?Ct value[\s:]+(\d+\.\d+)") if extract_with_regex(text, rf"{prefix}.*?Résultat[\s:]+Détecté") else None,
        f"pcr_{type_ecouv}_repete": extract_bool(text, rf"{prefix}.*?Test répété.*?0\s*Oui"),
        # Ajouter similaires pour repetition
    }

def parse_sample_collection(text):
    return {
        "date_prelevement": extract_with_regex(text, r"Date.?pr.l.vement.*?(\d{2}/\w{3}/\d{4})"),
        "heure_prelevement": extract_with_regex(text, r"à\s*\(?heure\)?[: ]+(\d{2}:\d{2})"),
        "sst_6ml": extract_with_regex(text, r"SST 6ml.*?x(\d+)"),
        "sst_2ml": extract_with_regex(text, r"SST 2ml.*?x(\d+)"),
        "edta_6ml": extract_with_regex(text, r"EDTA 6ml.*?x(\d+)"),
        "edta_2ml": extract_with_regex(text, r"EDTA 2ml.*?x(\d+)"),
        "heure_glaciere": extract_with_regex(text, r"Heure de mise en glacière[\s:]+(\d{2}:\d{2})"),
        "envoi_labo_date": extract_with_regex(text, r"Envoi au labo : date[\s& ]+(\d{2}/\w{3}/\d{4})"),
        "envoi_labo_heure": extract_with_regex(text, r"heure[\s:]+(\d{2}:\d{2})"),
        "initiales_collecteur": extract_with_regex(text, r"Initiales collecteur[\s:]+(\S+)"),
    }

def parse_lab_processing(text, type_sample="SST"):
    # Similaire pour chaque type: SST, EDTA, urine, etc.
    return {
        f"{type_sample.lower()}_date_prelevement": extract_with_regex(text, rf"{type_sample}.*?Date prélèvement.*?(\d{{2}}/\w{{3}}/\d{{4}})"),
        # Ajouter autres: arrivée, centrifugation, etc.
    }
    # Pour compléter, dupliquer pour chaque type

def parse_suivi(text, jour="J4"):
    return {
        f"suivi_{jour}_statut": extract_with_regex(text, rf"{jour}.*?Statut[\s:]+(Suivi|Perdu de vue|Décédé)"),
        f"suivi_{jour}_symptomes": extract_with_regex(text, rf"{jour}.*?Symptômes[\s:]+(Guérison|Amélioration|Stable|Détérioration)"),
        f"suivi_{jour}_date_visite": extract_with_regex(text, rf"{jour}.*?Date de visite.*?(\d{{2}}/\w{{3}}/\d{{4}})"),
        f"suivi_{jour}_commentaires": extract_with_regex(text, rf"{jour}.*?Commentaires\s*:\s*(.+?)(?:\n|$)") or "",
    }