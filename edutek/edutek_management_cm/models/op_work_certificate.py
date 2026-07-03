# -*- coding: utf-8 -*-
from odoo import api, fields, models


class OpWorkCertificate(models.Model):
    _name = "op.work.certificate"
    _description = "Certificat de travail"
    _order = "issue_date desc, id desc"

    name = fields.Char(string="Reference", default="/", readonly=True, copy=False)
    employee_id = fields.Many2one("hr.employee", string="Employe", required=True, ondelete="cascade")
    job_title = fields.Char(string="Fonction", related="employee_id.job_title", readonly=False)
    date_debut_emploi = fields.Date(string="En poste depuis")
    issue_date = fields.Date(string="Date d'emission", default=fields.Date.context_today)
    purpose = fields.Char(string="Motif de la demande")
    note = fields.Text(string="Note")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("op.work.certificate") or "/"
        return super().create(vals_list)
