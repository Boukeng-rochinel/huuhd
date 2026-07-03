# -*- coding: utf-8 -*-
from odoo import fields, models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    op_document_type_id = fields.Many2one(
        "op.document.type", string="Type de document (EduTek)", ondelete="cascade")
