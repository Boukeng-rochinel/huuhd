# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OpStudentSkillGenerateWizard(models.TransientModel):
    _name = "op.student.skill.generate.wizard"
    _description = "Preparer l'evaluation des acquis pour une classe"

    classe_id = fields.Many2one("op.classe", string="Classe", required=True)
    academic_year_id = fields.Many2one(
        "op.academic.year", related="classe_id.academic_year_id", readonly=True)
    classe_subject_id = fields.Many2one(
        "op.classe.subject", string="Domaine d'apprentissage", required=True,
        domain="[('classe_id', '=', classe_id)]")
    allowed_term_ids = fields.Many2many(
        "op.academic.term", compute="_compute_allowed_term_ids")
    academic_term_id = fields.Many2one(
        "op.academic.term", string="Periode", required=True,
        domain="[('id', 'in', allowed_term_ids)]")

    @api.depends("classe_id")
    def _compute_allowed_term_ids(self):
        for wizard in self:
            wizard.allowed_term_ids = (
                wizard.classe_id._get_applicable_terms() if wizard.classe_id else False)

    def action_generate(self):
        self.ensure_one()
        if self.academic_term_id not in self.classe_id._get_applicable_terms():
            raise UserError(_(
                "%(term)s ne fait pas partie des sequences applicables a "
                "la classe %(classe)s.",
                term=self.academic_term_id.display_name,
                classe=self.classe_id.display_name,
            ))
        Skill = self.env["op.student.skill"]
        for student in self.classe_id.student_ids:
            existing = Skill.search([
                ("student_id", "=", student.id),
                ("classe_subject_id", "=", self.classe_subject_id.id),
                ("academic_term_id", "=", self.academic_term_id.id),
            ], limit=1)
            if not existing:
                Skill.create({
                    "student_id": student.id,
                    "classe_subject_id": self.classe_subject_id.id,
                    "academic_term_id": self.academic_term_id.id,
                })

        return {
            "type": "ir.actions.act_window",
            "name": "Evaluation des acquis",
            "res_model": "op.student.skill",
            "view_mode": "list",
            "domain": [
                ("classe_subject_id", "=", self.classe_subject_id.id),
                ("academic_term_id", "=", self.academic_term_id.id),
            ],
            "context": {
                "default_classe_subject_id": self.classe_subject_id.id,
                "default_academic_term_id": self.academic_term_id.id,
            },
        }
