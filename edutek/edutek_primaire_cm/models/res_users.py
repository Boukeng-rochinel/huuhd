# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = "res.users"

    current_academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique en cours")

    @api.model
    def get_academic_year_switcher_data(self):
        """Donnees pour le selecteur d'annee academique (systray)."""
        years = self.env["op.academic.year"].search([], order="start_date desc")
        user = self.env.user
        current = user.current_academic_year_id
        if not current and years:
            current = years[0]
            user.current_academic_year_id = current
        return {
            "current_id": current.id if current else False,
            "current_name": current.name if current else False,
            "years": [{"id": y.id, "name": y.name} for y in years],
        }

    @api.model
    def set_current_academic_year(self, year_id):
        self.env.user.current_academic_year_id = year_id
        return True
