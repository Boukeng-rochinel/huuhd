# -*- coding: utf-8 -*-
from odoo import api, models


class ReportOpScholarship(models.AbstractModel):
    _name = "report.edutek_management_cm.report_scholarship_certificate"
    _description = "Certificat de bourse scolaire - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        scholarships = self.env["op.scholarship"].browse(docids)
        return {
            "doc_ids": docids,
            "doc_model": "op.scholarship",
            "docs": scholarships,
            "company": self.env.company,
            "lang_en": False,
        }
