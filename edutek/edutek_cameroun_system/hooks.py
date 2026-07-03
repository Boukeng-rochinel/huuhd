# -*- coding: utf-8 -*-
from datetime import date

MODULE = "edutek_cameroun_system"

# Libelle affiche dans le nom de la classe (ex: "CM2", "Form 5").
LEVEL_NAME = {
    "ps": "PS", "ms": "MS", "gs": "GS",
    "sil": "SIL", "cp": "CP", "ce1": "CE1", "ce2": "CE2",
    "cm1": "CM1", "cm2": "CM2",
    "6e": "6eme", "5e": "5eme", "4e": "4eme", "3e": "3eme",
    "2nde": "2nde", "1ere": "1ere", "terminale": "Terminale",
    "form1": "Form 1", "form2": "Form 2", "form3": "Form 3",
    "form4": "Form 4", "form5": "Form 5",
    "lower_sixth": "Lower Sixth", "upper_sixth": "Upper Sixth",
}

# (level_code, cycle, sous_systeme, series) - `series` est la liste des
# series officielles si ce niveau en comporte (1 classe par serie sera
# creee) ; None si le niveau n'a qu'une seule classe generique.
LEVELS = [
    # Maternelle
    ("ps", "maternelle", None, None),
    ("ms", "maternelle", None, None),
    ("gs", "maternelle", None, None),
    # Primaire
    ("sil", "primaire", None, None),
    ("cp", "primaire", None, None),
    ("ce1", "primaire", None, None),
    ("ce2", "primaire", None, None),
    ("cm1", "primaire", None, None),
    ("cm2", "primaire", None, None),
    # Secondaire francophone
    ("6e", "secondaire", "francophone", None),
    ("5e", "secondaire", "francophone", None),
    ("4e", "secondaire", "francophone", None),
    ("3e", "secondaire", "francophone", None),
    ("2nde", "secondaire", "francophone", None),
    ("1ere", "secondaire", "francophone", ["a4", "c", "d"]),
    ("terminale", "secondaire", "francophone", ["a4", "c", "d"]),
    # Secondaire anglophone
    ("form1", "secondaire", "anglophone", None),
    ("form2", "secondaire", "anglophone", None),
    ("form3", "secondaire", "anglophone", None),
    ("form4", "secondaire", "anglophone", None),
    ("form5", "secondaire", "anglophone", None),
    ("lower_sixth", "secondaire", "anglophone", ["sciences", "arts", "commercial"]),
    ("upper_sixth", "secondaire", "anglophone", ["sciences", "arts", "commercial"]),
]

# Lettre distinguant les classes d'un meme niveau quand celui-ci comporte
# plusieurs series officielles (1ere A4 / C / D, Lower Sixth Sciences /
# Arts / Commercial...).
SERIE_LETTERS = ["A", "B", "C"]

# (cle, nom, code, type)
SUBJECTS = [
    ("francais", "Francais", "FR", "theory"),
    ("maths", "Mathematiques", "MATH", "theory"),
    ("sciences", "Sciences d'Observation / SVT", "SCI", "theory"),
    ("hg", "Histoire - Geographie", "HG", "theory"),
    ("ecm", "Education Civique et Morale", "ECM", "theory"),
    ("anglais", "Anglais", "ANG", "theory"),
    ("eps", "Education Physique et Sportive", "EPS", "practical"),
    ("pc", "Physique - Chimie", "PC", "theory"),
    ("philo", "Philosophie", "PHILO", "theory"),
    ("lv2", "Espagnol (LV2)", "LV2", "theory"),
    ("langage", "Langage", "LANGAGE", "theory"),
    ("decouverte", "Decouverte du monde", "DECOUV", "theory"),
    ("arts", "Activites artistiques", "ARTS", "practical"),
    ("motricite", "Motricite", "MOTRI", "practical"),
    ("vivre", "Vivre ensemble", "VIVRE", "theory"),
]

# Programmes (cle matiere, coefficient) par cycle / niveau.
PROGRAMME_MATERNELLE = [
    ("langage", 1), ("decouverte", 1), ("arts", 1),
    ("motricite", 1), ("vivre", 1),
]
PROGRAMME_PRIMAIRE = [
    ("francais", 4), ("maths", 4), ("sciences", 2), ("hg", 2),
    ("ecm", 1), ("anglais", 2), ("eps", 1),
]
PROGRAMME_SECONDAIRE_COLLEGE = [
    ("francais", 3), ("maths", 4), ("pc", 3), ("sciences", 2),
    ("hg", 2), ("ecm", 1), ("anglais", 2), ("eps", 1), ("lv2", 2),
]
PROGRAMME_SECONDAIRE_LYCEE = PROGRAMME_SECONDAIRE_COLLEGE + [("philo", 2)]
LYCEE_PHILO_LEVELS = {"1ere", "terminale", "lower_sixth", "upper_sixth"}

N_TRIMESTRES = 3
SEQUENCES_PER_TRIMESTRE = 2


def _create_many_with_xmlid(env, model, vals_list, xml_ids):
    """Cree plusieurs enregistrements et leurs ir.model.data en une seule
    operation par lot, pour qu'ils soient proprement supprimes lors de la
    desinstallation du module (meme pattern que edutek_primaire_cm_demo)."""
    if not vals_list:
        return env[model]
    records = env[model].create(vals_list)
    env["ir.model.data"].create([
        {
            "name": xml_id,
            "module": MODULE,
            "model": model,
            "res_id": record.id,
            "noupdate": True,
        }
        for xml_id, record in zip(xml_ids, records)
    ])
    return records


def _current_school_year_bounds():
    """Annee scolaire camerounaise en cours (ou a venir) : commence le 1er
    septembre. Avant aout, on considere qu'on est encore dans l'annee
    scolaire qui a commence en septembre dernier."""
    today = date.today()
    start_year = today.year if today.month >= 8 else today.year - 1
    return date(start_year, 9, 1), date(start_year + 1, 6, 30)


def post_init_hook(env):
    """Met en place la structure de base d'une ecole camerounaise complete -
    maternelle, primaire et secondaire (francophone + anglophone) - decoupee
    en 3 trimestres de 2 sequences chacun par annee academique, SANS aucun
    eleve : annee academique, trimestres/sequences, matieres, types de
    frais, classes et leurs programmes. Les classes terminales de chaque
    cycle sont marquees 'classe d'examen' (elles s'arretent
    conventionnellement a la Sequence 5 - voir op.classe.applicable_term_ids
    dans edutek_primaire_cm pour le faire reellement prendre effet)."""

    if env.ref("%s.cameroun_academic_year" % MODULE, raise_if_not_found=False):
        return

    # ──────────────────────────────────────────────────────────
    # 1. Annee academique + 3 trimestres de 2 sequences chacun
    # ──────────────────────────────────────────────────────────
    start_date, end_date = _current_school_year_bounds()
    year_name = "%s-%s" % (start_date.year, end_date.year)

    year = env["op.academic.year"].search([("name", "=", year_name)], limit=1)
    if not year:
        year = _create_many_with_xmlid(env, "op.academic.year", [{
            "name": year_name,
            "start_date": start_date,
            "end_date": end_date,
        }], ["cameroun_academic_year"])[0]

    terms = year.academic_term_ids.sorted("sequence")
    if not terms:
        trimestre_bounds = env["op.academic.term"]._compute_trimestre_sequence_bounds(
            start_date, end_date, N_TRIMESTRES, SEQUENCES_PER_TRIMESTRE)

        trimestre_vals = [
            {
                "name": "Trimestre %d" % t_index,
                # 101, 102, 103... : volontairement hors de la plage 1..6
                # utilisee par les Sequences, pour ne jamais entrer en
                # collision avec les filtres "Sequence N" deja en place
                # dans les vues (op_student_mark_views.xml et consorts).
                "sequence": 100 + t_index,
                "academic_year_id": year.id,
                "term_start_date": bounds["start"],
                "term_end_date": bounds["end"],
            }
            for t_index, bounds in enumerate(trimestre_bounds, start=1)
        ]
        trimestres = _create_many_with_xmlid(
            env, "op.academic.term", trimestre_vals,
            ["cameroun_trimestre_%d" % i for i in range(1, N_TRIMESTRES + 1)])

        sequence_vals = []
        sequence_xmlids = []
        seq_counter = 0
        for t_index, bounds in enumerate(trimestre_bounds):
            for seq_bounds in bounds["sequences"]:
                seq_counter += 1
                sequence_vals.append({
                    "name": "Sequence %d" % seq_counter,
                    "sequence": seq_counter,
                    "academic_year_id": year.id,
                    "term_start_date": seq_bounds["start"],
                    "term_end_date": seq_bounds["end"],
                    "parent_term": trimestres[t_index].id,
                })
                sequence_xmlids.append("cameroun_term_%d" % seq_counter)
        terms = _create_many_with_xmlid(
            env, "op.academic.term", sequence_vals, sequence_xmlids)

    # ──────────────────────────────────────────────────────────
    # 2. Matieres / domaines d'apprentissage (reutilise si deja presentes)
    # ──────────────────────────────────────────────────────────
    Subject = env["op.subject"]
    subj = {}
    new_vals, new_xmlids, new_keys = [], [], []
    for key, name, code, subj_type in SUBJECTS:
        existing = Subject.search([("code", "=", code)], limit=1)
        if existing:
            subj[key] = existing
        else:
            new_vals.append({"name": name, "code": code, "type": subj_type})
            new_xmlids.append("cameroun_subject_%s" % key)
            new_keys.append(key)
    new_subjects = _create_many_with_xmlid(env, "op.subject", new_vals, new_xmlids)
    for key, record in zip(new_keys, new_subjects):
        subj[key] = record

    # ──────────────────────────────────────────────────────────
    # 3. Types de frais standards (Inscription, Pension...) - reutilise la
    #    logique deja en place pour toute societe utilisant edutek_primaire_cm
    #    (montant a 0, a definir depuis Configuration > Fiche de l'ecole)
    # ──────────────────────────────────────────────────────────
    env["op.fee.type"]._get_or_create_default_fee_types()

    # ──────────────────────────────────────────────────────────
    # 4. Classes : 1 classe par niveau (ou 1 par serie officielle pour les
    #    niveaux qui en comportent : 1ere/Terminale, Lower/Upper Sixth)
    # ──────────────────────────────────────────────────────────
    classes_vals = []
    classe_xmlids = []
    classe_meta = []  # (level_code, cycle)
    for level_code, cycle, sous_systeme, series in LEVELS:
        if series:
            for index, serie_code in enumerate(series):
                vals = {
                    "name": "%s %s" % (LEVEL_NAME[level_code], SERIE_LETTERS[index]),
                    "level": level_code,
                    "academic_year_id": year.id,
                    "serie": serie_code,
                }
                if sous_systeme:
                    vals["sous_systeme"] = sous_systeme
                classes_vals.append(vals)
                classe_xmlids.append("cameroun_classe_%s_%s" % (level_code, serie_code))
                classe_meta.append((level_code, cycle))
        else:
            vals = {
                "name": LEVEL_NAME[level_code],
                "level": level_code,
                "academic_year_id": year.id,
            }
            if sous_systeme:
                vals["sous_systeme"] = sous_systeme
            classes_vals.append(vals)
            classe_xmlids.append("cameroun_classe_%s" % level_code)
            classe_meta.append((level_code, cycle))

    classes = _create_many_with_xmlid(env, "op.classe", classes_vals, classe_xmlids)

    # ──────────────────────────────────────────────────────────
    # 5. Programme (op.classe.subject) par classe
    # ──────────────────────────────────────────────────────────
    classe_subject_vals = []
    for classe_index, (level_code, cycle) in enumerate(classe_meta):
        if cycle == "maternelle":
            programme = PROGRAMME_MATERNELLE
        elif cycle == "primaire":
            programme = PROGRAMME_PRIMAIRE
        elif level_code in LYCEE_PHILO_LEVELS:
            programme = PROGRAMME_SECONDAIRE_LYCEE
        else:
            programme = PROGRAMME_SECONDAIRE_COLLEGE

        for seq, (subject_key, coefficient) in enumerate(programme, start=1):
            classe_subject_vals.append({
                "classe_id": classes[classe_index].id,
                "subject_id": subj[subject_key].id,
                "coefficient": coefficient,
                "sequence": seq * 10,
            })
    env["op.classe.subject"].create(classe_subject_vals)
