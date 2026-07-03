# -*- coding: utf-8 -*-
from odoo import fields, models


class OpInternship(models.Model):
    _name = "op.internship"
    _inherit = ["op.academic.year.filter.mixin"]
    _description = "Stage eleve"
    _order = "date_debut desc, id desc"

    student_id = fields.Many2one("op.student", string="Eleve", required=True, ondelete="cascade")
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        default=lambda self: self.env.user.current_academic_year_id)

    title = fields.Char(string="Sujet du stage", required=True)
    host_organization = fields.Char(string="Structure d'accueil")
    supervisor_name = fields.Char(string="Superviseur")
    date_debut = fields.Date(string="Date de debut")
    date_fin = fields.Date(string="Date de fin")
    note = fields.Text(string="Note")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)
