# -*- coding: utf-8 -*-
from odoo import api, fields, models


class OpCarnet(models.Model):
    _name = "op.carnet"
    _description = "Carnet de suivi (maternelle)"
    _order = "academic_term_id desc, classe_id, student_id"
    _rec_name = "student_id"

    student_id = fields.Many2one(
        "op.student", string="Eleve", required=True, ondelete="cascade")
    classe_id = fields.Many2one(
        "op.classe", string="Classe", readonly=True,
        help="Classe de l'eleve au moment de la creation de ce carnet. "
             "Fixee une seule fois : un changement de classe ulterieur "
             "(promotion d'annee...) ne doit pas reecrire l'historique des "
             "carnets deja generes.")

    academic_term_id = fields.Many2one(
        "op.academic.term", string="Periode", required=True)
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        related="academic_term_id.academic_year_id", store=True, readonly=True)

    line_ids = fields.One2many("op.carnet.line", "carnet_id", string="Domaines evalues")

    assiduite = fields.Selection(
        [
            ("tres_bonne", "Tres bonne"),
            ("bonne", "Bonne"),
            ("irreguliere", "Irreguliere"),
        ],
        string="Assiduite", default="bonne")

    absences_justifiees = fields.Integer(string="Absences justifiees")
    absences_injustifiees = fields.Integer(string="Absences injustifiees")
    observation_generale = fields.Text(string="Observation generale")

    date_generation = fields.Datetime(string="Date de generation", readonly=True)

    _unique_student_term = models.Constraint(
        "unique(student_id, academic_term_id)",
        "Un carnet existe deja pour cet eleve et cette periode.")

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

    def action_print_carnet(self):
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_maternelle_cm.action_report_op_carnet", self)


class OpCarnetLine(models.Model):
    _name = "op.carnet.line"
    _description = "Ligne de carnet (evaluation par domaine)"
    _order = "sequence, id"

    carnet_id = fields.Many2one(
        "op.carnet", string="Carnet", required=True, ondelete="cascade")
    sequence = fields.Integer(string="Sequence", default=10)
    subject_id = fields.Many2one("op.subject", string="Domaine", required=True)
    niveau = fields.Selection(
        [
            ("acquis", "Acquis"),
            ("en_cours", "En cours d'acquisition"),
            ("non_acquis", "Non acquis"),
        ],
        string="Niveau")
    observation = fields.Char(string="Observation")
