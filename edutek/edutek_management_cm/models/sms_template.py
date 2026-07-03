# -*- coding: utf-8 -*-
from odoo import fields, models


class SmsTemplate(models.Model):
    _inherit = "sms.template"

    op_document_type_id = fields.Many2one(
        "op.document.type", string="Type de document (EduTek)", ondelete="cascade")
