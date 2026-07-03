# -*- coding: utf-8 -*-
from odoo import api, fields, models


class OpStudentDocument(models.Model):
    _name = "op.student.document"
    _description = "Piece scolaire fournie par un eleve"
    _order = "id"

    student_id = fields.Many2one("op.student", string="Eleve", required=True, ondelete="cascade")
    document_type_id = fields.Many2one(
        "op.school.document.type", string="Piece scolaire", required=True, ondelete="cascade")
    provided = fields.Boolean(string="Fournie")
    date_provided = fields.Date(string="Date de remise")
    note = fields.Char(string="Note")

    _sql_constraints = [
        ("student_document_type_uniq", "unique(student_id, document_type_id)",
         "Cette piece scolaire est deja suivie pour cet eleve."),
    ]

    @api.model
    def set_provided(self, student_id, document_type_id, provided):
        record = self.search([
            ("student_id", "=", student_id),
            ("document_type_id", "=", document_type_id),
        ], limit=1)
        vals = {
            "provided": provided,
            "date_provided": fields.Date.context_today(self) if provided else False,
        }
        if record:
            record.write(vals)
        else:
            vals.update({"student_id": student_id, "document_type_id": document_type_id})
            self.create(vals)
        return True
