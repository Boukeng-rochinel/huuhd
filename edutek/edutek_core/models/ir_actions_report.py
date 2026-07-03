# -*- coding: utf-8 -*-
import base64

from odoo import api, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def build_print_preview_action(self, xmlid, records, title=None, data=None, context=None):
        """Action client qui ouvre le previsualiseur d'impression EduTek
        (apercu + Imprimer/Telecharger) au lieu de declencher directement le
        telechargement PDF par defaut d'Odoo. `data` et `context` (optionnels)
        doivent rester json-serialisables : ils transitent vers le client puis
        reviennent par RPC pour le rendu et le telechargement (`context` permet
        par ex. de forcer `lang` pour un bulletin imprime en anglais)."""
        report = self.env.ref(xmlid)
        return {
            "type": "ir.actions.client",
            "tag": "edutek_core.print_preview",
            "target": "new",
            "name": title or report.name,
            "params": {
                "title": title or report.name,
                "report_xmlid": xmlid,
                "res_model": records._name,
                "res_ids": records.ids,
                "data": data or False,
                "context": context or False,
            },
        }

    @api.model
    def get_generic_report_action(self, xmlid, res_model, res_ids, data=None):
        """Reproduit le comportement standard d'Odoo (telechargement direct
        du PDF) pour le bouton 'Telecharger en PDF' du previsualiseur."""
        records = self.env[res_model].browse(res_ids)
        return self.env.ref(xmlid).report_action(records, data=data or None)

    @api.model
    def render_pdf_base64(self, xmlid, res_model, res_ids, data=None):
        """Rend le PDF du rapport en base64, pour l'aperçu integre dans le
        previsualiseur (sans passer par un telechargement de fichier).
        `_render_qweb_pdf` attend la reference du rapport en 1er argument et
        les ids en argument nomme `res_ids` - ce n'est pas une methode
        d'instance qu'on appelle sur un rapport deja resolu."""
        records = self.env[res_model].browse(res_ids)
        pdf_content, _report_type = self.env["ir.actions.report"]._render_qweb_pdf(
            xmlid, res_ids=records.ids, data=data or None)
        return base64.b64encode(pdf_content).decode()
