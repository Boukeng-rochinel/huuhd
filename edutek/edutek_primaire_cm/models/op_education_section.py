# -*- coding: utf-8 -*-
from odoo import fields, models


class OpEducationSection(models.Model):
    _name = "op.education.section"
    _description = "Sous-systeme / section (Francophone, Anglophone...)"
    _order = "sequence, name"

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(string="Code", required=True)
    sequence = fields.Integer(string="Sequence", default=10)

    _unique_code = models.Constraint("unique(code)", "Ce code de section existe deja.")
