# -*- coding: utf-8 -*-
from odoo import fields, models


class OpStaffType(models.Model):
    _name = "op.staff.type"
    _description = "Type de personnel"
    _order = "sequence, name"

    name = fields.Char(string="Nom", required=True)
    code = fields.Char(string="Code")
    sequence = fields.Integer(string="Sequence", default=10)
    company_id = fields.Many2one(
        "res.company", string="Societe", default=lambda self: self.env.company)

    _unique_name = models.Constraint(
        "unique(name)", "Ce type de personnel existe deja.")
