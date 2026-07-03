# -*- coding: utf-8 -*-
from odoo import models


class OpBulletin(models.Model):
    _inherit = "op.bulletin"

    def action_print_bulletin(self):
        action = super().action_print_bulletin()
        if len(self) == 1 and self.classe_id.sous_systeme == "anglophone":
            # Imprime le "Report Card" en anglais quelle que soit la langue
            # de l'utilisateur connecte (necessite que la langue Anglais (US)
            # soit installee / active sur la base).
            action = dict(action)
            params = dict(action.get("params") or {})
            params["context"] = {"lang": "en_US"}
            action["params"] = params
        return action
