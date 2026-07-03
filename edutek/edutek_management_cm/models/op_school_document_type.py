# -*- coding: utf-8 -*-
from odoo import fields, models


class OpSchoolDocumentType(models.Model):
    _name = "op.school.document.type"
    _description = "Type de piece scolaire requise"
    _order = "sequence, name"

    name = fields.Char(string="Piece scolaire", required=True)
    code = fields.Char(string="Code", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(default=True)
