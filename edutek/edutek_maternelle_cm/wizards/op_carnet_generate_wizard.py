# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OpCarnetGenerateWizard(models.TransientModel):
    _name = "op.carnet.generate.wizard"
    _description = "Generer les carnets de suivi d'une classe"

    classe_id = fields.Many2one("op.classe", string="Classe", required=True)
    academic_year_id = fields.Many2one(
        "op.academic.year", related="classe_id.academic_year_id", readonly=True)
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
        Carnet = self.env["op.carnet"]

        for student in self.classe_id.student_ids:
            carnet = Carnet.search([
                ("student_id", "=", student.id),
                ("academic_term_id", "=", self.academic_term_id.id),
            ], limit=1)
            if not carnet:
                carnet = Carnet.create({
                    "student_id": student.id,
                    "academic_term_id": self.academic_term_id.id,
                })

            carnet.line_ids.unlink()
            line_vals = []
            for classe_subject in self.classe_id.subject_line_ids:
                skill = Skill.search([
                    ("student_id", "=", student.id),
                    ("classe_subject_id", "=", classe_subject.id),
                    ("academic_term_id", "=", self.academic_term_id.id),
                ], limit=1)
                line_vals.append((0, 0, {
                    "subject_id": classe_subject.subject_id.id,
                    "sequence": classe_subject.sequence,
                    "niveau": skill.niveau if skill else False,
                    "observation": skill.observation if skill else False,
                }))
            carnet.write({
                "line_ids": line_vals,
                "date_generation": fields.Datetime.now(),
            })

        return {
            "type": "ir.actions.act_window",
            "name": "Carnets de suivi",
            "res_model": "op.carnet",
            "view_mode": "list,form",
            "domain": [
                ("classe_id", "=", self.classe_id.id),
                ("academic_term_id", "=", self.academic_term_id.id),
            ],
        }
