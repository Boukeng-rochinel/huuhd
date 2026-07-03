# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ReportStudentInsolvable(models.AbstractModel):
    _name = "report.edutek_primaire_cm.student_insolvable"
    _description = "Etat des insolvables - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        wizards = self.env["op.student.insolvable.wizard"].browse(docids)
        wizard = wizards[:1]
        lines = wizard._get_insolvable_lines() if wizard else []

        groups = []
        current_classe = None
        current_lines = None
        for line in lines:
            classe = line["classe"]
            if classe != current_classe:
                current_classe = classe
                current_lines = []
                groups.append({"classe": classe, "lines": current_lines})
            current_lines.append(line)

        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.student.insolvable.wizard",
            "docs": wizards,
            "company": self.env.company,
            "lang_en": False,
            "now": now,
            "groups": groups,
            "effectif": len(lines),
            "total_du": sum(line["montant_du"] for line in lines),
            "total_verse": sum(line["montant_verse"] for line in lines),
            "total_reste": sum(line["reste"] for line in lines),
        }
