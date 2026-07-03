# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ReportOpBulletin(models.AbstractModel):
    _name = "report.edutek_primaire_cm.report_bulletin_document"
    _description = "Bulletin trimestriel - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        bulletins = self.env["op.bulletin"].browse(docids)
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.bulletin",
            "docs": bulletins,
            "company": self.env.company,
            "lang_en": False,
            "now": now,
        }
