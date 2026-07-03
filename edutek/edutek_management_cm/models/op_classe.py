# -*- coding: utf-8 -*-
from odoo import api, fields, models

_CONFIG_SELECTION_FIELDS = ["level", "serie", "deuxieme_langue", "determinant_reussite", "type_bulletin"]

_CONFIG_LIST_FIELDS = [
    "name", "level", "serie", "deuxieme_langue", "intitule_abrege",
    "moy_min_passage_trimestre", "moy_min_passage_annee",
    "bulletin_double", "bulletin_multi_pages", "determinant_reussite",
    "type_bulletin", "student_count", "matricule_prefix", "teacher_id",
]


class OpClasse(models.Model):
    _inherit = "op.classe"

    intitule_abrege = fields.Char(string="Intitule abrege")
    deuxieme_langue = fields.Selection(
        [
            ("anglais", "Anglais"),
            ("francais", "Francais"),
            ("espagnol", "Espagnol"),
            ("allemand", "Allemand"),
        ],
        string="2eme langue",
    )

    moy_min_passage_trimestre = fields.Float(
        string="Moy. min de passage (par periode)", default=10.0)
    moy_min_passage_annee = fields.Float(
        string="Moy. min de passage (annee)", default=10.0)

    bulletin_double = fields.Boolean(string="Classe avec deux bulletins")
    bulletin_multi_pages = fields.Boolean(string="Bulletin sur plusieurs pages")

    determinant_reussite = fields.Selection(
        [
            ("annuel", "Resultat annuel"),
            ("trimestre", "Moyenne de la derniere periode"),
            ("cumul", "Cumul des periodes"),
        ],
        string="Determinant de reussite", default="annuel",
    )
    type_bulletin = fields.Selection(
        [
            ("defaut", "Bulletin par defaut"),
            ("simplifie", "Bulletin simplifie"),
        ],
        string="Type de bulletin", default="defaut",
    )

    @api.model
    def get_classe_config_bootstrap(self):
        """Donnees necessaires a l'ecran 'Fiche de l'ecole > Classe' : options
        des champs de selection (fusionnees depuis tous les modules installes)
        et la liste des classes de l'annee academique en cours, en un seul
        appel pour eviter les allers-retours depuis le composant OWL."""
        fields_info = self.fields_get(_CONFIG_SELECTION_FIELDS, attributes=["selection"])
        selections = {fname: info["selection"] for fname, info in fields_info.items()}

        classes = self.search_read([], _CONFIG_LIST_FIELDS)
        class_ids = [c["id"] for c in classes]

        fee_lines = self.env["op.classe.fee"].search_read(
            [("classe_id", "in", class_ids)], ["classe_id", "fee_type_id", "amount"])
        fee_types = self.env["op.fee.type"].search_read([], ["name"])
        employees = self.env["hr.employee"].sudo().search_read(
            [("active", "=", True)], ["name", "sis_role"], order="name")

        year = self.env.user.current_academic_year_id
        return {
            "selections": selections,
            "current_year_id": year.id if year else False,
            "classes": classes,
            "fee_lines": fee_lines,
            "fee_types": fee_types,
            "employees": employees,
        }
