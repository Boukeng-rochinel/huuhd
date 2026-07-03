# -*- coding: utf-8 -*-
from odoo import fields, models


class OpStudentEnrollmentHistory(models.Model):
    _name = "op.student.enrollment.history"
    _description = "Historique d'inscription annuelle d'un eleve"
    _order = "academic_year_id desc"

    student_id = fields.Many2one(
        "op.student", string="Eleve", required=True, ondelete="cascade", index=True)
    classe_id = fields.Many2one("op.classe", string="Classe", required=True)
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        related="classe_id.academic_year_id", store=True, index=True)
    date_inscription = fields.Date(
        string="Date d'inscription", default=fields.Date.context_today, required=True,
        help="Date a laquelle l'eleve a ete inscrit pour cette annee academique. "
             "Fixee une seule fois a la creation ; un changement de classe en cours "
             "d'annee ne la modifie pas.")

    mark_count = fields.Integer(compute="_compute_counts", string="Nb notes")
    bulletin_count = fields.Integer(compute="_compute_counts", string="Nb bulletins")
    fee_count = fields.Integer(compute="_compute_counts", string="Nb frais")

    _unique_student_year = models.Constraint(
        "unique(student_id, academic_year_id)",
        "Un historique existe deja pour cet eleve sur cette annee academique.")

    def _compute_counts(self):
        for record in self:
            domain = [
                ("student_id", "=", record.student_id.id),
                ("academic_year_id", "=", record.academic_year_id.id),
            ]
            record.mark_count = self.env["op.student.mark"].search_count(domain)
            record.bulletin_count = self.env["op.bulletin"].search_count(domain)
            record.fee_count = self.env["op.student.fee"].search_count(domain)

    def action_view_marks(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Notes",
            "res_model": "op.student.mark",
            "view_mode": "list",
            "domain": [
                ("student_id", "=", self.student_id.id),
                ("academic_year_id", "=", self.academic_year_id.id),
            ],
        }

    def action_view_bulletins(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Bulletins",
            "res_model": "op.bulletin",
            "view_mode": "kanban,list,form",
            "domain": [
                ("student_id", "=", self.student_id.id),
                ("academic_year_id", "=", self.academic_year_id.id),
            ],
        }

    def action_view_fees(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Frais scolaires",
            "res_model": "op.student.fee",
            "view_mode": "kanban,list,form",
            "domain": [
                ("student_id", "=", self.student_id.id),
                ("academic_year_id", "=", self.academic_year_id.id),
            ],
        }
