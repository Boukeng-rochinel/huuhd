# -*- coding: utf-8 -*-
from odoo import fields, models


class OpScholarship(models.Model):
    _name = "op.scholarship"
    _inherit = ["op.academic.year.filter.mixin"]
    _description = "Bourse scolaire"
    _order = "date_debut desc, id desc"

    student_id = fields.Many2one("op.student", string="Eleve", required=True, ondelete="cascade")
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique", required=True,
        default=lambda self: self.env.user.current_academic_year_id)

    scholarship_type = fields.Selection(
        [("totale", "Totale"), ("partielle", "Partielle")],
        string="Type de bourse", default="partielle", required=True)
    percentage = fields.Float(string="Pourcentage de prise en charge")
    amount = fields.Monetary(string="Montant fixe")
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", string="Devise")

    date_debut = fields.Date(string="Date de debut", default=fields.Date.context_today)
    date_fin = fields.Date(string="Date de fin")
    reason = fields.Text(string="Motif")
    state = fields.Selection(
        [("draft", "Brouillon"), ("active", "Active"), ("ended", "Terminee")],
        string="Statut", default="draft", required=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)

    def action_activate(self):
        self.write({"state": "active"})

    def action_end(self):
        self.write({"state": "ended", "date_fin": fields.Date.context_today(self)})

    def action_print_certificate(self):
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_management_cm.action_report_op_scholarship", self)
