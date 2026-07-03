# -*- coding: utf-8 -*-
from odoo import api, fields, models


class OpClasse(models.Model):
    _inherit = "op.classe"

    skill_count = fields.Integer(compute="_compute_maternelle_counts", string="Nb evaluations")
    carnet_count = fields.Integer(compute="_compute_maternelle_counts", string="Nb carnets")

    @api.depends("student_ids")
    def _compute_maternelle_counts(self):
        for record in self:
            record.skill_count = self.env["op.student.skill"].search_count(
                [("classe_id", "=", record.id)])
            record.carnet_count = self.env["op.carnet"].search_count(
                [("classe_id", "=", record.id)])

    def action_view_skills(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Evaluations",
            "res_model": "op.student.skill",
            "view_mode": "list",
            "domain": [("classe_id", "=", self.id)],
            "context": {"search_default_group_term": 1},
        }

    def action_view_carnets(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Carnets de suivi",
            "res_model": "op.carnet",
            "view_mode": "kanban,list,form",
            "domain": [("classe_id", "=", self.id)],
            "context": {"search_default_group_term": 1},
        }

    def action_open_skill_generate_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Evaluer les acquis",
            "res_model": "op.student.skill.generate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_classe_id": self.id},
        }

    def action_open_carnet_generate_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Generer les carnets",
            "res_model": "op.carnet.generate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_classe_id": self.id},
        }
