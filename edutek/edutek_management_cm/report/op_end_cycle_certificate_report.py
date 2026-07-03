# -*- coding: utf-8 -*-
from odoo import api, fields, models

CYCLE_LABEL_FR = {
    "maternelle": "Maternelle",
    "primaire": "Primaire",
    "secondaire": "Secondaire",
}
CYCLE_LABEL_EN = {
    "maternelle": "Nursery",
    "primaire": "Primary",
    "secondaire": "Secondary",
}


class ReportOpEndCycleCertificate(models.AbstractModel):
    _name = "report.edutek_management_cm.report_promotion_cert"
    _description = "Certificat / attestation de promotion - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        certificates = self.env["op.end.cycle.certificate"].browse(docids)
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.end.cycle.certificate",
            "docs": certificates,
            "company": self.env.company,
            "now": now,
            "cycle_label_fr": CYCLE_LABEL_FR,
            "cycle_label_en": CYCLE_LABEL_EN,
        }


class ReportOpEndCycleCertificate2up(models.AbstractModel):
    _name = "report.edutek_management_cm.report_promotion_cert_2up"
    _description = "Certificat / attestation de promotion (2 par page) - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        certificates = self.env["op.end.cycle.certificate"].browse(docids)
        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        pairs = [
            (certificates[i], certificates[i + 1] if i + 1 < len(certificates) else False)
            for i in range(0, len(certificates), 2)
        ]
        return {
            "doc_ids": docids,
            "doc_model": "op.end.cycle.certificate",
            "docs": certificates,
            "company": self.env.company,
            "now": now,
            "cycle_label_fr": CYCLE_LABEL_FR,
            "cycle_label_en": CYCLE_LABEL_EN,
            "pairs": pairs,
        }
