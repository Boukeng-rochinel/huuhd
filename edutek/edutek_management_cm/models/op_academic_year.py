# -*- coding: utf-8 -*-
from odoo import fields, models


class OpAcademicYear(models.Model):
    _inherit = "op.academic.year"

    is_closed = fields.Boolean(
        string="Annee cloturee", default=False,
        help="Coche automatiquement par l'assistant de cloture d'annee "
             "(Vie scolaire > Cloturer une annee academique), pour empecher "
             "de cloturer deux fois la meme annee.")
