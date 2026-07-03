# -*- coding: utf-8 -*-
from odoo import api, fields, models

EXAM_LEVELS = {"cm2", "3e", "terminale", "form5", "upper_sixth"}


class OpClasse(models.Model):
    _inherit = "op.classe"

    is_exam_class = fields.Boolean(
        string="Classe d'examen", compute="_compute_is_exam_class", store=True,
        help="Classe terminale d'un cycle, sanctionnee par un examen national "
             "(CEP, BEPC, Probatoire/Bac, GCE O-Level/A-Level). Par convention, "
             "ces classes s'arretent a la Sequence 5 : la Sequence 6 est "
             "consacree aux examens et n'est pas evaluee en interne.")

    @api.depends("level")
    def _compute_is_exam_class(self):
        for record in self:
            record.is_exam_class = record.level in EXAM_LEVELS
