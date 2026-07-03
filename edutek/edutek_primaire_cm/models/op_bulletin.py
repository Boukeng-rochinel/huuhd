# -*- coding: utf-8 -*-
from odoo import api, fields, models


class OpBulletin(models.Model):
    _name = "op.bulletin"
    _description = "Bulletin trimestriel"
    _order = "academic_term_id desc, classe_id, rang"
    _rec_name = "student_id"

    student_id = fields.Many2one(
        "op.student", string="Eleve", required=True, ondelete="cascade")
    classe_id = fields.Many2one(
        "op.classe", string="Classe", readonly=True,
        help="Classe de l'eleve au moment de la generation de ce bulletin. "
             "Fixee une seule fois : un changement de classe ulterieur "
             "(promotion d'annee...) ne doit pas reecrire l'historique des "
             "bulletins deja generes.")

    academic_term_id = fields.Many2one(
        "op.academic.term", string="Periode", required=True)
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        related="academic_term_id.academic_year_id", store=True, readonly=True)

    line_ids = fields.One2many("op.bulletin.line", "bulletin_id", string="Notes")

    total_coef = fields.Float(string="Total coefficients", compute="_compute_totals", store=True)
    total_points = fields.Float(string="Total points", compute="_compute_totals", store=True)
    moyenne_generale = fields.Float(
        string="Moyenne generale / 20", compute="_compute_totals", store=True, digits=(16, 2))

    rang = fields.Integer(string="Rang", readonly=True)
    effectif_classe = fields.Integer(string="Effectif de la classe", readonly=True)
    moyenne_classe = fields.Float(
        string="Moyenne de la classe", readonly=True, digits=(16, 2))

    appreciation = fields.Char(string="Appreciation generale")
    conduite = fields.Selection(
        [
            ("excellente", "Excellente"),
            ("tres_bonne", "Tres bonne"),
            ("bonne", "Bonne"),
            ("passable", "Passable"),
            ("mediocre", "Mediocre"),
        ],
        string="Conduite", default="bonne")

    absences_justifiees = fields.Integer(string="Absences justifiees")
    absences_injustifiees = fields.Integer(string="Absences injustifiees")
    decision = fields.Char(string="Decision")

    date_generation = fields.Datetime(string="Date de generation", readonly=True)

    _unique_student_term = models.Constraint(
        "unique(student_id, academic_term_id)",
        "Un bulletin existe deja pour cet eleve et cette periode.")

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

    @api.depends("line_ids.note", "line_ids.coefficient", "line_ids.note_x_coef")
    def _compute_totals(self):
        for record in self:
            total_coef = sum(record.line_ids.mapped("coefficient"))
            total_points = sum(record.line_ids.mapped("note_x_coef"))
            record.total_coef = total_coef
            record.total_points = total_points
            record.moyenne_generale = (total_points / total_coef) if total_coef else 0.0

    def action_print_bulletin(self):
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_op_bulletin", self)


class OpBulletinLine(models.Model):
    _name = "op.bulletin.line"
    _description = "Ligne de bulletin (note par matiere)"
    _order = "sequence, id"

    bulletin_id = fields.Many2one(
        "op.bulletin", string="Bulletin", required=True, ondelete="cascade")
    sequence = fields.Integer(string="Sequence", default=10)
    subject_id = fields.Many2one("op.subject", string="Matiere", required=True)
    coefficient = fields.Float(string="Coefficient", default=1.0)
    note = fields.Float(string="Note / 20", digits=(16, 2))
    note_x_coef = fields.Float(
        string="Note x Coef", compute="_compute_note_x_coef", store=True, digits=(16, 2))

    @api.depends("note", "coefficient")
    def _compute_note_x_coef(self):
        for record in self:
            record.note_x_coef = record.note * record.coefficient
