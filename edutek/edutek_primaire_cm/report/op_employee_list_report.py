# -*- coding: utf-8 -*-
from odoo import api, fields, models

STAFF_TYPE_LABELS = {
    "non_enseignant": "Non enseignant",
    "enseignant_permanent": "Enseignant permanent",
    "enseignant_vacataire": "Enseignant vacataire",
}


class ReportOpEmployeeList(models.AbstractModel):
    _name = "report.edutek_primaire_cm.report_employee_list_document"
    _description = "Liste du personnel - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        wizards = self.env["op.employee.list.wizard"].browse(docids)
        wizard = wizards[:1]
        employees = wizard._get_employees() if wizard else self.env["hr.employee"]
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.employee.list.wizard",
            "docs": wizards,
            "company": self.env.company,
            "lang_en": False,
            "now": now,
            "employees": employees,
            "staff_type_labels": STAFF_TYPE_LABELS,
        }
