# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class OpAdmissionApplication(models.Model):
    _name = "op.admission.application"
    _description = "Candidature / demande d'admission"
    _order = "application_date desc, id desc"

    applicant_name = fields.Char(string="Nom du candidat", required=True)
    birth_date = fields.Date(string="Date de naissance")
    gender = fields.Selection(
        [("m", "Masculin"), ("f", "Feminin"), ("o", "Autre")], string="Sexe", default="m")

    desired_classe_id = fields.Many2one("op.classe", string="Classe souhaitee")
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        default=lambda self: self.env.user.current_academic_year_id)

    parent_name = fields.Char(string="Nom du parent / tuteur")
    parent_phone = fields.Char(string="Telephone du parent")
    parent_email = fields.Char(string="Email du parent")

    application_date = fields.Date(string="Date de la demande", default=fields.Date.context_today)
    decision_date = fields.Date(string="Date de decision")
    state = fields.Selection(
        [("pending", "En attente"), ("accepted", "Acceptee"), ("rejected", "Rejetee")],
        string="Statut", default="pending", required=True)
    note = fields.Text(string="Note")

    student_id = fields.Many2one(
        "op.student", string="Eleve cree", readonly=True, copy=False,
        help="Renseigne automatiquement lorsque la candidature est convertie en eleve.")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)

    def action_accept(self):
        self.write({"state": "accepted", "decision_date": fields.Date.context_today(self)})

    def action_reject(self):
        self.write({"state": "rejected", "decision_date": fields.Date.context_today(self)})

    def action_create_student(self):
        self.ensure_one()
        if self.state != "accepted":
            raise UserError(_("Seule une candidature acceptee peut etre convertie en eleve."))
        if self.student_id:
            raise UserError(_("Cette candidature a deja ete convertie en eleve."))

        name_parts = (self.applicant_name or "").split(" ", 1)
        first_name = name_parts[0] if name_parts else self.applicant_name
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        student = self.env["op.student"].create({
            "first_name": first_name,
            "last_name": last_name,
            "gender": self.gender or "m",
            "birth_date": self.birth_date,
            "email": self.parent_email,
            "classe_id": self.desired_classe_id.id if self.desired_classe_id else False,
        })
        self.student_id = student.id
        return {
            "type": "ir.actions.act_window",
            "res_model": "op.student",
            "view_mode": "form",
            "res_id": student.id,
        }
