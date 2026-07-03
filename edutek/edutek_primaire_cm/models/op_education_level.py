# -*- coding: utf-8 -*-
from odoo import fields, models


class OpEducationLevel(models.Model):
    _name = "op.education.level"
    _description = "Niveau scolaire (SIL, CP, CE1, 6eme, Form 1...)"
    _order = "sequence, name"

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(
        string="Code", required=True,
        help="Valeur technique stockee sur les classes utilisant ce niveau "
             "(ex: 'ce2'). Ne pas modifier apres la creation des premieres "
             "classes : renommer le 'Nom' suffit a changer le libelle affiche.")
    sequence = fields.Integer(
        string="Sequence", default=10,
        help="Determine l'ordre de tri des classes (du plus jeune au plus "
             "avance).")
    cycle_id = fields.Many2one(
        "op.education.cycle", string="Cycle", required=True, ondelete="cascade")
    section_id = fields.Many2one(
        "op.education.section", string="Section",
        help="Sous-systeme francophone/anglophone de ce niveau.")

    _unique_code = models.Constraint("unique(code)", "Ce code de niveau existe deja.")
