# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ReportStudentRegistrationList(models.AbstractModel):
    _name = "report.edutek_primaire_cm.report_registration_list"
    _description = "Liste des eleves inscrits - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        wizards = self.env["op.student.registration.list.wizard"].browse(docids)
        wizard = wizards[:1]
        groups = wizard._get_grouped_lines() if wizard else []
        gender_counts = wizard._get_gender_counts() if wizard else {"m": 0, "f": 0}
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.student.registration.list.wizard",
            "docs": wizards,
            "company": self.env.company,
            "lang_en": False,
            "groups": groups,
            "is_new_for_year": wizard._is_new_for_year if wizard else (lambda s: False),
            "gender_counts": gender_counts,
            "now": now,
        }
