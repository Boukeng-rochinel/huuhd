# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ReportOpCarnet(models.AbstractModel):
    _name = "report.edutek_maternelle_cm.report_carnet_document"
    _description = "Carnet de suivi - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        carnets = self.env["op.carnet"].browse(docids)
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.carnet",
            "docs": carnets,
            "company": self.env.company,
            "lang_en": False,
            "now": now,
        }
