# -*- coding: utf-8 -*-
from odoo import api, fields, models


class OpStudentSkill(models.Model):
    _name = "op.student.skill"
    _description = "Evaluation par competences (maternelle)"
    _order = "academic_term_id desc, classe_subject_id, student_id"
    _rec_name = "classe_subject_id"

    student_id = fields.Many2one(
        "op.student", string="Eleve", required=True, ondelete="cascade")
    classe_id = fields.Many2one(
        "op.classe", string="Classe", readonly=True,
        help="Classe de l'eleve au moment de la creation de cette "
             "evaluation. Fixee une seule fois : un changement de classe "
             "ulterieur (promotion d'annee...) ne doit pas reecrire "
             "l'historique des evaluations deja saisies.")

    academic_term_id = fields.Many2one(
        "op.academic.term", string="Periode", required=True)
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        related="academic_term_id.academic_year_id", store=True, readonly=True)

    classe_subject_id = fields.Many2one(
        "op.classe.subject", string="Domaine d'apprentissage", required=True,
        ondelete="restrict",
        domain="[('classe_id', '=', classe_id)]")
    subject_id = fields.Many2one(
        "op.subject", string="Domaine",
        related="classe_subject_id.subject_id", store=True, readonly=True)

    niveau = fields.Selection(
        [
            ("acquis", "Acquis"),
            ("en_cours", "En cours d'acquisition"),
            ("non_acquis", "Non acquis"),
        ],
        string="Niveau", required=True, default="en_cours")
    observation = fields.Char(string="Observation")

    _unique_student_subject_term = models.Constraint(
        "unique(student_id, classe_subject_id, academic_term_id)",
        "Une evaluation existe deja pour cet eleve, ce domaine et cette periode.")

    @api.onchange("student_id")
    def _onchange_student_id(self):
        if self.student_id:
            self.classe_id = self.student_id.classe_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("classe_id") and vals.get("student_id"):
                student = self.env["op.student"].browse(vals["student_id"])
                if student.classe_id:
                    vals["classe_id"] = student.classe_id.id
        return super().create(vals_list)
