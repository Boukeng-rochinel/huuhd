# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ReportStudentBonafide(models.AbstractModel):
    _name = "report.edutek_core.report_student_bonafide"
    _description = "Bonafide certificate - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        students = self.env["op.student"].browse(docids)
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.student",
            "docs": students,
            "data": data,
            "company": self.env.company,
            "lang_en": True,
            "now": now,
        }
