# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OpFeeReduction(models.Model):
    _name = "op.fee.reduction"
    _inherit = ["op.academic.year.filter.mixin"]
    _description = "Réduction de scolarité"
    _order = "date_debut desc, id desc"

    student_id = fields.Many2one(
        "op.student", string="Élève", required=True, ondelete="cascade")
    classe_id = fields.Many2one(
        "op.classe", string="Classe",
        related="student_id.classe_id", store=True, readonly=True)
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Année académique", required=True,
        default=lambda self: self.env.user.current_academic_year_id)

    reduction_type = fields.Selection(
        [("montant", "Montant fixe"), ("pourcentage", "Pourcentage")],
        string="Type de réduction", default="montant", required=True)
    amount = fields.Monetary(
        string="Montant de la réduction",
        help="Montant fixe déduit des frais générés pour cet élève.")
    percentage = fields.Float(
        string="Pourcentage (%)",
        help="Pourcentage de réduction appliqué sur le montant total des frais.")
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", string="Devise")

    date_debut = fields.Date(
        string="Date de début", default=fields.Date.context_today)
    date_fin = fields.Date(string="Date de fin")
    reason = fields.Text(string="Motif de la réduction")
    state = fields.Selection(
        [("draft", "Brouillon"), ("active", "Active"), ("ended", "Terminée")],
        string="Statut", default="draft", required=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)

    @api.onchange("reduction_type")
    def _onchange_reduction_type(self):
        if self.reduction_type == "pourcentage":
            self.amount = 0.0
        else:
            self.percentage = 0.0

    def _compute_effective_amount(self):
        """Retourne le montant de réduction effectif à appliquer sur le dossier
        de l'élève, calculé selon le type (montant fixe ou pourcentage du total
        des frais de la classe)."""
        self.ensure_one()
        if self.reduction_type == "montant":
            return self.amount
        if self.reduction_type == "pourcentage" and self.student_id.classe_id:
            total = sum(
                line.amount
                for line in self.student_id.classe_id.fee_line_ids
                if line.amount > 0
            )
            return round(total * self.percentage / 100.0, 2)
        return 0.0

    def action_activate(self):
        for rec in self:
            if rec.state != "draft":
                continue
            effective = rec._compute_effective_amount()
            if effective <= 0:
                raise UserError(_(
                    "Le montant calculé de la réduction est nul ou négatif. "
                    "Vérifiez le montant ou le pourcentage saisi."))
            rec.student_id.discount_amount = effective
            rec.write({
                "state": "active",
                "amount": effective if rec.reduction_type == "pourcentage" else rec.amount,
            })

    def action_end(self):
        for rec in self:
            if rec.state != "active":
                continue
            rec.student_id.discount_amount = 0.0
            rec.write({
                "state": "ended",
                "date_fin": fields.Date.context_today(self),
            })
