# -*- coding: utf-8 -*-
from odoo import api, fields, models

_BOOTSTRAP_TYPE_FIELDS = [
    "name", "code", "channel", "model_id", "model_name", "default_body_fr", "default_body_en"]
_BOOTSTRAP_MAIL_TEMPLATE_FIELDS = ["name", "lang", "op_document_type_id"]
_BOOTSTRAP_SMS_TEMPLATE_FIELDS = ["name", "op_document_type_id"]


class OpDocumentType(models.Model):
    _name = "op.document.type"
    _description = "Type de document ou de courrier"
    _order = "sequence, name"

    name = fields.Char(string="Type de message / document", required=True)
    code = fields.Char(string="Code", required=True)
    sequence = fields.Integer(string="Sequence", default=10)

    channel = fields.Selection(
        [("mail", "Email / Lettre"), ("sms", "SMS")],
        string="Canal", default="mail", required=True)

    model_id = fields.Many2one(
        "ir.model", string="Modele cible", required=True, ondelete="cascade",
        help="Enregistrement sur lequel les champs de fusion du modele sont resolus "
             "(eleve, facture, classe, employe...).")
    model_name = fields.Char(related="model_id.model", string="Modele technique", store=True)

    default_body_fr = fields.Html(string="Modele initial (Francais)")
    default_body_en = fields.Html(string="Modele initial (Anglais)")

    template_ids = fields.One2many(
        "mail.template", "op_document_type_id", string="Modeles personnalises (email/lettre)")
    sms_template_ids = fields.One2many(
        "sms.template", "op_document_type_id", string="Modeles personnalises (SMS)")
    template_count = fields.Integer(compute="_compute_template_count", string="Nb modeles")

    @api.depends("template_ids", "sms_template_ids")
    def _compute_template_count(self):
        for record in self:
            record.template_count = len(record.template_ids) + len(record.sms_template_ids)

    @api.model
    def get_doc_template_bootstrap(self):
        """Donnees pour l'ecran 'Fiche de l'ecole > Options > Modele' : la
        liste des types de document et, pour chacun, ses modeles
        personnalises (mail.template ou sms.template selon le canal), en un
        seul appel."""
        types = self.search_read([], _BOOTSTRAP_TYPE_FIELDS)
        type_ids = [t["id"] for t in types]

        mail_templates = self.env["mail.template"].search_read(
            [("op_document_type_id", "in", type_ids)], _BOOTSTRAP_MAIL_TEMPLATE_FIELDS)
        for tmpl in mail_templates:
            tmpl["is_sms"] = False

        sms_templates = self.env["sms.template"].search_read(
            [("op_document_type_id", "in", type_ids)], _BOOTSTRAP_SMS_TEMPLATE_FIELDS)
        for tmpl in sms_templates:
            tmpl["is_sms"] = True
            tmpl["lang"] = False

        return {"types": types, "templates": mail_templates + sms_templates}
