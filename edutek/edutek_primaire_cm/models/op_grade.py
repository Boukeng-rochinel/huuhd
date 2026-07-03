# -*- coding: utf-8 -*-
from odoo import fields, models


class OpGrade(models.Model):
    _name = "op.grade"
    _description = "Grade du personnel"
    _order = "sequence, name"

    name = fields.Char(string="Nom", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    company_id = fields.Many2one(
        "res.company", string="Societe", default=lambda self: self.env.company)

    _unique_name = models.Constraint(
        "unique(name)", "Ce grade existe deja.")
