# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ReportOpClasseList(models.AbstractModel):
    _name = "report.edutek_primaire_cm.report_classe_list_document"
    _description = "Liste des classes - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        wizards = self.env["op.classe.list.wizard"].browse(docids)
        wizard = wizards[:1]
        classes = wizard._get_classes() if wizard else self.env["op.classe"]
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.classe.list.wizard",
            "docs": wizards,
            "company": self.env.company,
            "lang_en": False,
            "now": now,
            "classes": classes,
            "level_labels": dict(wizard._selection_level()) if wizard else {},
            "cycle_labels": dict(wizard._selection_cycle()) if wizard else {},
        }
