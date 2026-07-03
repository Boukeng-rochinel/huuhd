# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ReportBulletinList(models.AbstractModel):
    _name = "report.edutek_primaire_cm.report_bulletin_list_document"
    _description = "Classement des bulletins - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        wizards = self.env["op.bulletin.list.wizard"].browse(docids)
        wizard = wizards[:1]
        bulletins = wizard._get_bulletins() if wizard else self.env["op.bulletin"]
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.bulletin.list.wizard",
            "docs": wizards,
            "company": self.env.company,
            "lang_en": False,
            "now": now,
            "bulletins": bulletins,
            "conduite_labels": dict(self.env["op.bulletin"]._fields["conduite"].selection),
        }
