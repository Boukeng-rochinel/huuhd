# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ReportStudentFeeList(models.AbstractModel):
    _name = "report.edutek_primaire_cm.report_student_fee_list_document"
    _description = "Liste des frais - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        wizards = self.env["op.student.fee.list.wizard"].browse(docids)
        wizard = wizards[:1]
        fees = wizard._get_fees() if wizard else self.env["op.student.fee"]
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.student.fee.list.wizard",
            "docs": wizards,
            "company": self.env.company,
            "lang_en": False,
            "now": now,
            "fees": fees,
            "payment_state_labels": {
                "not_paid": "Non paye", "partial": "Partiel", "paid": "Paye",
                "in_payment": "En cours", "reversed": "Annule",
            },
        }
