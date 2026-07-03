# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class OpStudentFee(models.Model):
    _inherit = "op.student.fee"

    moratorium_ids = fields.One2many(
        "op.payment.moratorium", "fee_id", string="Moratoires")
    active_moratorium_id = fields.Many2one(
        "op.payment.moratorium", string="Moratoire en cours",
        compute="_compute_due_date", store=True)
    due_date = fields.Date(
        string="Date limite de paiement", compute="_compute_due_date", store=True,
        help="Echeance du moratoire si un moratoire a ete accorde, sinon la "
             "date limite configuree sur le type de frais, sinon la date du "
             "frais.")

    @api.depends("date", "fee_type_id.date_limite",
                 "moratorium_ids.state", "moratorium_ids.new_due_date")
    def _compute_due_date(self):
        for rec in self:
            moratorium = rec.moratorium_ids.filtered(
                lambda m: m.state == "approved").sorted("new_due_date", reverse=True)[:1]
            rec.active_moratorium_id = moratorium
            if moratorium:
                rec.due_date = moratorium.new_due_date
            else:
                rec.due_date = rec.fee_type_id.date_limite or rec.date

    def _get_recap_lines(self):
        """Reprend la logique d'edutek_primaire_cm mais affiche la date limite
        reelle (echeance du moratoire si un moratoire est accorde) et signale
        les tranches concernees par un moratoire."""
        self.ensure_one()
        fees = self.search([
            ("student_id", "=", self.student_id.id),
            ("academic_year_id", "=", self.academic_year_id.id),
            ("state", "=", "posted"),
        ], order="academic_term_id, fee_type_id")
        lines = []
        for fee in fees:
            tranche = fee.academic_term_id.name if fee.academic_term_id else _("Inscription")
            lines.append({
                "label": "%s : %s" % (tranche, fee.fee_type_id.name),
                "date": fee.due_date,
                "tarif": fee.amount,
                "paye": fee.amount - fee.amount_residual,
                "reste": fee.amount_residual,
                "moratorium": bool(fee.active_moratorium_id),
            })
        return lines
