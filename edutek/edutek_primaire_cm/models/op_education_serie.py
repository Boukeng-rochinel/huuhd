# -*- coding: utf-8 -*-
from odoo import fields, models


class OpEducationSerie(models.Model):
    _name = "op.education.serie"
    _description = "Serie du secondaire (A4, C, D, Arts, Sciences...)"
    _order = "sequence, name"

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(string="Code", required=True)
    sequence = fields.Integer(string="Sequence", default=10)

    _unique_code = models.Constraint("unique(code)", "Ce code de serie existe deja.")
