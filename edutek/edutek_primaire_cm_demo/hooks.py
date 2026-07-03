# -*- coding: utf-8 -*-
import random
from datetime import date

MODULE = "edutek_primaire_cm_demo"

SECTIONS = ["A", "B", "C"]

# Libelle affiche dans le nom de la classe (ex: "CM2 A", "Form 5 B").
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

# (level_code, cycle, sous_systeme, series_par_section, age_en_2026)
LEVELS = [
    # Maternelle
    ("ps", "maternelle", None, None, 3),
    ("ms", "maternelle", None, None, 4),
    ("gs", "maternelle", None, None, 5),
    # Primaire
    ("sil", "primaire", None, None, 6),
    ("cp", "primaire", None, None, 6),
    ("ce1", "primaire", None, None, 7),
    ("ce2", "primaire", None, None, 8),
    ("cm1", "primaire", None, None, 9),
    ("cm2", "primaire", None, None, 10),
    # Secondaire francophone
    ("6e", "secondaire", "francophone", None, 11),
    ("5e", "secondaire", "francophone", None, 12),
    ("4e", "secondaire", "francophone", None, 13),
    ("3e", "secondaire", "francophone", None, 14),
    ("2nde", "secondaire", "francophone", None, 15),
    ("1ere", "secondaire", "francophone", ["a4", "c", "d"], 16),
    ("terminale", "secondaire", "francophone", ["a4", "c", "d"], 17),
    # Secondaire anglophone
    ("form1", "secondaire", "anglophone", None, 11),
    ("form2", "secondaire", "anglophone", None, 12),
    ("form3", "secondaire", "anglophone", None, 13),
    ("form4", "secondaire", "anglophone", None, 14),
    ("form5", "secondaire", "anglophone", None, 15),
    ("lower_sixth", "secondaire", "anglophone", ["sciences", "arts", "commercial"], 16),
    ("upper_sixth", "secondaire", "anglophone", ["sciences", "arts", "commercial"], 17),
]

# (xml_id_suffix, nom, code, type)
SUBJECTS = [
    ("francais", "Francais", "DEMO-FR", "theory"),
    ("maths", "Mathematiques", "DEMO-MATH", "theory"),
    ("sciences", "Sciences d'Observation / SVT", "DEMO-SCI", "theory"),
    ("hg", "Histoire - Geographie", "DEMO-HG", "theory"),
    ("ecm", "Education Civique et Morale", "DEMO-ECM", "theory"),
    ("anglais", "Anglais", "DEMO-ANG", "theory"),
    ("eps", "Education Physique et Sportive", "DEMO-EPS", "practical"),
    ("pc", "Physique - Chimie", "DEMO-PC", "theory"),
    ("philo", "Philosophie", "DEMO-PHILO", "theory"),
    ("lv2", "Espagnol (LV2)", "DEMO-LV2", "theory"),
    ("langage", "Langage", "DEMO-LANGAGE", "theory"),
    ("decouverte", "Decouverte du monde", "DEMO-DECOUV", "theory"),
    ("arts", "Activites artistiques", "DEMO-ARTS", "practical"),
    ("motricite", "Motricite", "DEMO-MOTRI", "practical"),
    ("vivre", "Vivre ensemble", "DEMO-VIVRE", "theory"),
]

# Programmes (cle matiere, coefficient) par cycle.
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

N_STUDENTS_PAR_CLASSE = 4

FIRST_NAMES_M = [
    "Junior", "Patrick", "Cedric", "Steve", "Eric", "Franck", "Herve",
    "Yannick", "Arnaud", "Bruno", "Christian", "Davy", "Emmanuel",
    "Fabrice", "Gerald", "Hugo", "Ivan", "Joel", "Kevin", "Landry",
]
FIRST_NAMES_F = [
    "Carine", "Aurelie", "Brenda", "Sandrine", "Chantal", "Diane",
    "Estelle", "Florence", "Grace", "Huguette", "Irene", "Jocelyne",
    "Karine", "Linda", "Marlyse", "Nadege", "Olive", "Patricia",
    "Queen", "Rosine",
]
LAST_NAMES = [
    "Ndongo", "Mballa", "Fotso", "Ngono", "Eyenga", "Talla", "Mbarga",
    "Kamga", "Nkomo", "Tchamba", "Abena", "Biya", "Etoundi", "Fokou",
    "Gueye", "Hamadou", "Issa", "Kuate", "Loum", "Manga", "Nana",
    "Owona", "Pemha", "Sango", "Tabi", "Um", "Vondou", "Wandji",
    "Yomba", "Zang",
]

NIVEAUX_COMPETENCE = ["acquis", "en_cours", "non_acquis"]


def _create_many_with_xmlid(env, model, vals_list, xml_ids):
    """Cree plusieurs enregistrements et leurs ir.model.data en une seule
    operation par lot, pour qu'ils soient proprement supprimes lors de la
    desinstallation du module (sans dependre de la cle 'demo' du manifeste,
    qui n'est pas chargee sur une base sans donnees de demo)."""
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


def post_init_hook(env):
    """Genere une ecole camerounaise complete de demonstration : maternelle,
    primaire et secondaire (francophone + anglophone), 3 sections (A/B/C)
    par niveau, avec programmes, eleves, notes / evaluations et frais
    scolaires. Tout est cree via l'ORM (et trace dans ir.model.data dans
    un ordre qui permet une suppression propre par cascade a la
    desinstallation)."""

    if env.ref("%s.demo_academic_year" % MODULE, raise_if_not_found=False):
        return

    # ──────────────────────────────────────────────────────────
    # 1. Annee academique + trimestres
    # ──────────────────────────────────────────────────────────
    year = _create_many_with_xmlid(env, "op.academic.year", [{
        "name": "2026-2027",
        "start_date": date(2026, 9, 1),
        "end_date": date(2027, 6, 30),
        "term_structure": "three_sem",
    }], ["demo_academic_year"])[0]

    term1, term2, term3 = _create_many_with_xmlid(env, "op.academic.term", [
        {
            "name": "Trimestre 1",
            "sequence": 1,
            "academic_year_id": year.id,
            "term_start_date": date(2026, 9, 1),
            "term_end_date": date(2026, 11, 30),
        },
        {
            "name": "Trimestre 2",
            "sequence": 2,
            "academic_year_id": year.id,
            "term_start_date": date(2026, 12, 1),
            "term_end_date": date(2027, 3, 15),
        },
        {
            "name": "Trimestre 3",
            "sequence": 3,
            "academic_year_id": year.id,
            "term_start_date": date(2027, 3, 16),
            "term_end_date": date(2027, 6, 30),
        },
    ], ["demo_term_1", "demo_term_2", "demo_term_3"])

    # ──────────────────────────────────────────────────────────
    # 2. Matieres / domaines d'apprentissage
    # ──────────────────────────────────────────────────────────
    subject_records = _create_many_with_xmlid(
        env, "op.subject",
        [{"name": s[1], "code": s[2], "type": s[3]} for s in SUBJECTS],
        ["demo_subject_%s" % s[0] for s in SUBJECTS],
    )
    subj = {s[0]: rec for s, rec in zip(SUBJECTS, subject_records)}

    # ──────────────────────────────────────────────────────────
    # 3. Types de frais (depend du plan comptable installe)
    # ──────────────────────────────────────────────────────────
    income_account = env["account.account"].search([
        ("account_type", "in", ("income", "income_other")),
        ("company_ids", "in", env.company.id),
    ], limit=1)
    sale_journal = env["account.journal"].search([
        ("type", "=", "sale"),
        ("company_id", "=", env.company.id),
    ], limit=1)

    fee_type_inscription = fee_type_scolarite = None
    if income_account and sale_journal:
        fee_type_inscription, fee_type_scolarite = _create_many_with_xmlid(
            env, "op.fee.type",
            [
                {
                    "name": "Frais d'inscription",
                    "code": "INSCRIPTION",
                    "amount": 25000.0,
                    "account_id": income_account.id,
                },
                {
                    "name": "Scolarite - Trimestre 1",
                    "code": "SCOLARITE-T1",
                    "amount": 50000.0,
                    "account_id": income_account.id,
                },
            ],
            ["demo_fee_type_inscription", "demo_fee_type_scolarite_t1"],
        )

    # ──────────────────────────────────────────────────────────
    # 4. Classes : tous les niveaux x sections A/B/C
    # ──────────────────────────────────────────────────────────
    classes_vals = []
    classe_xmlids = []
    classe_meta = []  # (level_code, cycle, age)
    for level_code, cycle, sous_systeme, series, age in LEVELS:
        for index, section in enumerate(SECTIONS):
            vals = {
                "name": "%s %s" % (LEVEL_NAME[level_code], section),
                "level": level_code,
                "academic_year_id": year.id,
            }
            if sous_systeme:
                vals["sous_systeme"] = sous_systeme
            if series:
                vals["serie"] = series[index]
            classes_vals.append(vals)
            classe_xmlids.append("demo_classe_%s_%s" % (level_code, section.lower()))
            classe_meta.append((level_code, cycle, age))

    classes = _create_many_with_xmlid(env, "op.classe", classes_vals, classe_xmlids)

    # ──────────────────────────────────────────────────────────
    # 5. Programme (op.classe.subject) par classe
    # ──────────────────────────────────────────────────────────
    classe_subject_vals = []
    classe_subject_index = []  # (classe_index, subject_key)
    classe_programme = {}  # classe_index -> [subject_key, ...]
    for classe_index, (level_code, cycle, age) in enumerate(classe_meta):
        if cycle == "maternelle":
            programme = PROGRAMME_MATERNELLE
        elif cycle == "primaire":
            programme = PROGRAMME_PRIMAIRE
        elif level_code in LYCEE_PHILO_LEVELS:
            programme = PROGRAMME_SECONDAIRE_LYCEE
        else:
            programme = PROGRAMME_SECONDAIRE_COLLEGE

        classe_programme[classe_index] = [key for key, _coef in programme]
        for sequence, (subject_key, coefficient) in enumerate(programme, start=1):
            classe_subject_vals.append({
                "classe_id": classes[classe_index].id,
                "subject_id": subj[subject_key].id,
                "coefficient": coefficient,
                "sequence": sequence * 10,
            })
            classe_subject_index.append((classe_index, subject_key))

    classe_subjects = env["op.classe.subject"].create(classe_subject_vals)
    classe_subject_map = {
        key: record for key, record in zip(classe_subject_index, classe_subjects)
    }

    # ──────────────────────────────────────────────────────────
    # 6. Eleves (4 par classe, tous niveaux)
    # ──────────────────────────────────────────────────────────
    cameroun_id = env.ref("base.cm").id

    students_vals = []
    student_xmlids = []
    student_meta = []  # (classe_index, level_code, cycle)
    counter = 0
    for classe_index, (level_code, cycle, age) in enumerate(classe_meta):
        birth_year = 2026 - age
        for _i in range(N_STUDENTS_PAR_CLASSE):
            counter += 1
            gender = "m" if counter % 2 else "f"
            first_names = FIRST_NAMES_M if gender == "m" else FIRST_NAMES_F
            first_name = first_names[counter % len(first_names)]
            last_name = LAST_NAMES[(counter * 7) % len(LAST_NAMES)]
            month = 1 + (counter % 12)
            day = 1 + (counter % 27)
            students_vals.append({
                "name": "%s %s" % (first_name, last_name),
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "birth_date": date(birth_year, month, day),
                "gr_no": "DEMO-%04d" % counter,
                "country_id": cameroun_id,
                "nationality": cameroun_id,
                "classe_id": classes[classe_index].id,
            })
            student_xmlids.append("demo_student_%04d" % counter)
            student_meta.append((classe_index, level_code, cycle))

    no_mail_env = env(context=dict(
        env.context,
        tracking_disable=True,
        mail_create_nolog=True,
        mail_create_nosubscribe=True,
        mail_auto_subscribe=False,
    ))
    students = _create_many_with_xmlid(
        no_mail_env, "op.student", students_vals, student_xmlids)

    # ──────────────────────────────────────────────────────────
    # 7. Notes (primaire + secondaire, les 3 trimestres)
    # ──────────────────────────────────────────────────────────
    marks_vals = []
    for term_index, term in enumerate((term1, term2, term3)):
        random.seed(42 + term_index)
        for student_index, (classe_index, level_code, cycle) in enumerate(student_meta):
            if cycle == "maternelle":
                continue
            student = students[student_index]
            for subject_key in classe_programme[classe_index]:
                classe_subject = classe_subject_map[(classe_index, subject_key)]
                marks_vals.append({
                    "student_id": student.id,
                    "academic_term_id": term.id,
                    "classe_subject_id": classe_subject.id,
                    "note": round(random.uniform(8, 18), 2),
                })
    env["op.student.mark"].create(marks_vals)

    # ──────────────────────────────────────────────────────────
    # 8. Evaluations par competences (maternelle, les 3 trimestres)
    # ──────────────────────────────────────────────────────────
    skills_vals = []
    for term_index, term in enumerate((term1, term2, term3)):
        for student_index, (classe_index, level_code, cycle) in enumerate(student_meta):
            if cycle != "maternelle":
                continue
            student = students[student_index]
            for domain_index, subject_key in enumerate(classe_programme[classe_index]):
                classe_subject = classe_subject_map[(classe_index, subject_key)]
                base_index = (student_index + domain_index) % 3
                niveau_index = max(0, base_index - term_index)
                skills_vals.append({
                    "student_id": student.id,
                    "academic_term_id": term.id,
                    "classe_subject_id": classe_subject.id,
                    "niveau": NIVEAUX_COMPETENCE[niveau_index],
                })
    env["op.student.skill"].create(skills_vals)

    # ──────────────────────────────────────────────────────────
    # 9. Frais des eleves (brouillon)
    # ──────────────────────────────────────────────────────────
    if fee_type_inscription and fee_type_scolarite:
        fees_vals = []
        for student_index, student in enumerate(students):
            fees_vals.append({
                "student_id": student.id,
                "academic_year_id": year.id,
                "academic_term_id": term1.id,
                "fee_type_id": fee_type_inscription.id,
                "date": year.start_date,
                "amount": fee_type_inscription.amount,
                "currency_id": fee_type_inscription.currency_id.id,
                "journal_id": sale_journal.id,
            })
            if student_index % 2 == 0:
                fees_vals.append({
                    "student_id": student.id,
                    "academic_year_id": year.id,
                    "academic_term_id": term1.id,
                    "fee_type_id": fee_type_scolarite.id,
                    "date": year.start_date,
                    "amount": fee_type_scolarite.amount,
                    "currency_id": fee_type_scolarite.currency_id.id,
                    "journal_id": sale_journal.id,
                })
        env["op.student.fee"].create(fees_vals)
