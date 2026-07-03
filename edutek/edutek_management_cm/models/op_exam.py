# -*- coding: utf-8 -*-
from odoo import fields, models


class OpExam(models.Model):
    _name = "op.exam"
    _inherit = ["op.academic.year.filter.mixin"]
    _description = "Examen ou concours"
    _order = "date desc, id desc"

    name = fields.Char(string="Intitule", required=True)
    exam_type = fields.Selection(
        [
            ("examen", "Examen"),
            ("concours", "Concours"),
        ],
        string="Type", default="examen", required=True,
    )
    classe_id = fields.Many2one("op.classe", string="Classe")
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        default=lambda self: self.env.user.current_academic_year_id)
    date = fields.Date(string="Date")
    note = fields.Text(string="Note")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)
