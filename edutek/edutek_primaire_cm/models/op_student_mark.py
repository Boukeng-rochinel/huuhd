# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class OpStudentMark(models.Model):
    _name = "op.student.mark"
    _description = "Note d'un eleve"
    _order = "academic_term_id desc, classe_subject_id, student_id"
    _rec_name = "subject_id"

    student_id = fields.Many2one(
        "op.student", string="Eleve", required=True, ondelete="cascade")
    classe_id = fields.Many2one(
        "op.classe", string="Classe", readonly=True,
        help="Classe de l'eleve au moment de la creation de cette note. "
             "Fixee une seule fois : un changement de classe ulterieur "
             "(promotion d'annee...) ne doit pas reecrire l'historique des "
             "notes deja saisies.")

    academic_term_id = fields.Many2one(
        "op.academic.term", string="Periode", required=True)
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        related="academic_term_id.academic_year_id", store=True, readonly=True)

    classe_subject_id = fields.Many2one(
        "op.classe.subject", string="Matiere (programme)", required=True,
        ondelete="restrict",
        domain="[('classe_id', '=', classe_id)]")
    subject_id = fields.Many2one(
        "op.subject", string="Matiere",
        related="classe_subject_id.subject_id", store=True, readonly=True)
    coefficient = fields.Float(
        string="Coefficient",
        related="classe_subject_id.coefficient", store=True, readonly=True)

    note = fields.Float(string="Note / 20", required=True, default=0.0)
    note_x_coef = fields.Float(
        string="Note x Coef", compute="_compute_note_x_coef", store=True)

    _unique_student_subject_term = models.Constraint(
        "unique(student_id, classe_subject_id, academic_term_id)",
        "Une note existe deja pour cet eleve, cette matiere et cette periode.")

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

    @api.depends("note", "coefficient")
    def _compute_note_x_coef(self):
        for record in self:
            record.note_x_coef = record.note * record.coefficient

    @api.constrains("note")
    def _check_note_range(self):
        for record in self:
            if record.note < 0 or record.note > 20:
                raise ValidationError(_("La note doit etre comprise entre 0 et 20."))
