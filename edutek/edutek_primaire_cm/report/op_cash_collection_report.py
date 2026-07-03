# -*- coding: utf-8 -*-
from odoo import api, fields, models


def _common_values(self, docids):
    wizards = self.env["op.cash.collection.wizard"].browse(docids)
    wizard = wizards[:1]
    rows = wizard._get_rows() if wizard else []
    summary = wizard._get_summary(rows) if wizard else {}
    now = fields.Datetime.context_timestamp(
        self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
    return {
        "doc_ids": docids,
        "docs": wizards,
        "company": self.env.company,
        "lang_en": False,
        "now": now,
        "rows": rows,
        "summary": summary,
    }


class ReportOpCashCollectionDaily(models.AbstractModel):
    _name = "report.edutek_primaire_cm.report_cash_daily"
    _description = "Etat des encaissements par jour - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        values = _common_values(self, docids)
        values["doc_model"] = "op.cash.collection.wizard"
        return values


class ReportOpCashCollectionLedger(models.AbstractModel):
    _name = "report.edutek_primaire_cm.report_cash_ledger"
    _description = "Etat des encaissements (detaille) - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        values = _common_values(self, docids)
        values["doc_model"] = "op.cash.collection.wizard"
        return values
