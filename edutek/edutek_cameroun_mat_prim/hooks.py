# -*- coding: utf-8 -*-
from datetime import date

MODULE = "edutek_cameroun_mat_prim"

SUBJECTS = [
    ("francais",   "Francais",                    "FR",      "theory"),
    ("maths",      "Mathematiques",               "MATH",    "theory"),
    ("sciences",   "Sciences d'Observation / SVT","SCI",     "theory"),
    ("hg",         "Histoire - Geographie",       "HG",      "theory"),
    ("ecm",        "Education Civique et Morale", "ECM",     "theory"),
    ("anglais",    "Anglais",                     "ANG",     "theory"),
    ("eps",        "Education Physique et Sportive","EPS",   "practical"),
    ("langage",    "Langage",                     "LANGAGE", "theory"),
    ("decouverte", "Decouverte du monde",         "DECOUV",  "theory"),
    ("arts",       "Activites artistiques",       "ARTS",    "practical"),
    ("motricite",  "Motricite",                   "MOTRI",   "practical"),
    ("vivre",      "Vivre ensemble",              "VIVRE",   "theory"),
]

N_TRIMESTRES = 3
SEQUENCES_PER_TRIMESTRE = 2


def _create_many_with_xmlid(env, model, vals_list, xml_ids):
    if not vals_list:
        return env[model]
    records = env[model].create(vals_list)
    env["ir.model.data"].create([
        {"name": xml_id, "module": MODULE, "model": model,
         "res_id": record.id, "noupdate": True}
        for xml_id, record in zip(xml_ids, records)
    ])
    return records


def _current_school_year_bounds():
    today = date.today()
    start_year = today.year if today.month >= 8 else today.year - 1
    return date(start_year, 9, 1), date(start_year + 1, 6, 30)


def post_init_hook(env):
    if env.ref("%s.academic_year" % MODULE, raise_if_not_found=False):
        return

    # 1. Annee academique + trimestres / sequences
    start_date, end_date = _current_school_year_bounds()
    year_name = "%s-%s" % (start_date.year, end_date.year)
    year = env["op.academic.year"].search([("name", "=", year_name)], limit=1)
    if not year:
        year = _create_many_with_xmlid(env, "op.academic.year", [{
            "name": year_name,
            "start_date": start_date,
            "end_date": end_date,
        }], ["academic_year"])[0]

    if not year.academic_term_ids:
        bounds = env["op.academic.term"]._compute_trimestre_sequence_bounds(
            start_date, end_date, N_TRIMESTRES, SEQUENCES_PER_TRIMESTRE)

        trimestre_vals = [
            {"name": "Trimestre %d" % i,
             "sequence": 100 + i,
             "academic_year_id": year.id,
             "term_start_date": b["start"],
             "term_end_date": b["end"]}
            for i, b in enumerate(bounds, start=1)
        ]
        trimestres = _create_many_with_xmlid(
            env, "op.academic.term", trimestre_vals,
            ["trimestre_%d" % i for i in range(1, N_TRIMESTRES + 1)])

        seq_vals, seq_xmlids, seq_num = [], [], 0
        for t_idx, b in enumerate(bounds):
            for sb in b["sequences"]:
                seq_num += 1
                seq_vals.append({
                    "name": "Sequence %d" % seq_num,
                    "sequence": seq_num,
                    "academic_year_id": year.id,
                    "term_start_date": sb["start"],
                    "term_end_date": sb["end"],
                    "parent_term": trimestres[t_idx].id,
                })
                seq_xmlids.append("sequence_%d" % seq_num)
        _create_many_with_xmlid(env, "op.academic.term", seq_vals, seq_xmlids)

    # 2. Matieres
    Subject = env["op.subject"]
    for key, name, code, subj_type in SUBJECTS:
        if not Subject.search([("code", "=", code)], limit=1):
            _create_many_with_xmlid(env, "op.subject",
                [{"name": name, "code": code, "type": subj_type}],
                ["subject_%s" % key])

    # 3. Types de frais standards
    env["op.fee.type"]._get_or_create_default_fee_types()
