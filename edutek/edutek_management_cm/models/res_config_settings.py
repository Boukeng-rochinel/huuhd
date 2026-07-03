# -*- coding: utf-8 -*-
from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    use_scholarships = fields.Boolean(
        string="Bourses scolaires",
        help="Affiche le menu Bourses scolaires dans le module EduTek.")
    use_fee_reductions = fields.Boolean(
        string="Réductions de scolarité",
        help="Affiche le menu Réductions de scolarité dans le module EduTek.")
    use_moratoriums = fields.Boolean(
        string="Moratoires de paiement",
        help="Affiche le menu Moratoires de paiement dans le module EduTek.")
    use_bank_receipts = fields.Boolean(
        string="Reçus bancaires (scanner OCR)",
        help="Affiche le menu Reçus bancaires permettant le scan et la "
             "gestion des reçus physiques avant encaissement.")
    use_admissions = fields.Boolean(
        string="Admissions / Candidatures",
        help="Affiche le menu Admissions / Candidatures dans le module EduTek.")

    def _feature_group_map(self):
        return {
            "use_scholarships": "edutek_management_cm.group_use_scholarships",
            "use_fee_reductions": "edutek_management_cm.group_use_fee_reductions",
            "use_moratoriums": "edutek_management_cm.group_use_moratoriums",
            "use_bank_receipts": "edutek_management_cm.group_use_bank_receipts",
            "use_admissions": "edutek_management_cm.group_use_admissions",
        }

    def _sync_feature_group(self, field_name, enabled):
        """Grant (or revoke) a feature group via group implication on admin group."""
        group_xmlid = self._feature_group_map().get(field_name)
        if not group_xmlid:
            return
        group = self.env.ref(group_xmlid, raise_if_not_found=False)
        admin_group = self.env.ref(
            "edutek_core.group_op_back_office_admin", raise_if_not_found=False)
        if not group or not admin_group:
            return
        if enabled:
            admin_group.sudo().write({"implied_ids": [(4, group.id)]})
        else:
            admin_group.sudo().write({"implied_ids": [(3, group.id)]})

    def set_values(self):
        super().set_values()
        param = self.env["ir.config_parameter"].sudo()
        for fname in self._feature_group_map():
            val = bool(getattr(self, fname))
            param.set_param("edutek.%s" % fname, str(val))
            self._sync_feature_group(fname, val)

    def get_values(self):
        res = super().get_values()
        param = self.env["ir.config_parameter"].sudo().get_param
        for fname in self._feature_group_map():
            raw = param("edutek.%s" % fname, "True")
            res[fname] = raw == "True"
        return res
