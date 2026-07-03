# -*- coding: utf-8 -*-
from odoo import api, models


class ReportStudentIdCard(models.AbstractModel):
    _name = "report.edutek_core.report_student_idcard"
    _description = "Carte scolaire - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get("active_model") or "op.student"
        docs = self.env[model].browse(self.env.context.get("active_ids") or docids)
        show_photo = self.env["ir.config_parameter"].sudo().get_param(
            "edutek_primaire_cm.show_photo_on_student_card", "True") in ("True", "1")
        return {
            "doc_ids": docids,
            "doc_model": model,
            "docs": docs,
            "show_photo": show_photo,
        }
