# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ReportStudentMarkList(models.AbstractModel):
    _name = "report.edutek_primaire_cm.report_student_mark_list_document"
    _description = "Liste des notes - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        wizards = self.env["op.student.mark.list.wizard"].browse(docids)
        wizard = wizards[:1]
        marks = wizard._get_marks() if wizard else self.env["op.student.mark"]
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.student.mark.list.wizard",
            "docs": wizards,
            "company": self.env.company,
            "lang_en": False,
            "now": now,
            "marks": marks,
        }
