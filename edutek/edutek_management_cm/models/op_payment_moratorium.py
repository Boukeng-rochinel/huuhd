# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OpPaymentMoratorium(models.Model):
    _name = "op.payment.moratorium"
    _description = "Moratoire de paiement"
    _order = "create_date desc"

    fee_id = fields.Many2one("op.student.fee", string="Frais concerne", required=True, ondelete="cascade")
    student_id = fields.Many2one(
        "op.student", string="Eleve", related="fee_id.student_id", store=True, readonly=True)
    original_amount = fields.Monetary(
        string="Montant initial", related="fee_id.amount", store=True, readonly=True)
    currency_id = fields.Many2one(
        "res.currency", related="fee_id.currency_id", string="Devise")

    new_due_date = fields.Date(string="Nouvelle echeance", required=True)
    reason = fields.Text(string="Motif")
    decision_date = fields.Date(string="Date de decision", default=fields.Date.context_today)
    state = fields.Selection(
        [("draft", "Brouillon"), ("approved", "Approuve"), ("closed", "Cloture")],
        string="Statut", default="draft", required=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)

    @api.constrains("new_due_date")
    def _check_new_due_date(self):
        for record in self:
            if record.new_due_date and record.fee_id.date and record.new_due_date <= record.fee_id.date:
                raise UserError(_("La nouvelle echeance doit etre posterieure a la date du frais initial."))

    def action_approve(self):
        self.write({"state": "approved"})

    def action_close(self):
        self.write({"state": "closed"})
