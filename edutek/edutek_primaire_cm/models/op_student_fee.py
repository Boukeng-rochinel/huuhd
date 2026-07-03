# -*- coding: utf-8 -*-
import base64
import io

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    import qrcode
except ImportError:
    qrcode = None

try:
    from num2words import num2words
except ImportError:
    num2words = None


class OpStudentFee(models.Model):
    _name = "op.student.fee"
    _description = "Frais scolaire d'un eleve"
    _order = "date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Reference", default="/", readonly=True, copy=False, tracking=True)

    student_id = fields.Many2one(
        "op.student", string="Eleve", required=True, ondelete="cascade", tracking=True)
    partner_id = fields.Many2one(
        "res.partner", string="Tiers (facturation)",
        related="student_id.partner_id", store=True, readonly=True)
    classe_id = fields.Many2one(
        "op.classe", string="Classe", readonly=True,
        help="Classe de l'eleve au moment de la creation de ce frais. "
             "Fixee une seule fois (champ stocke, non lie en direct a la "
             "classe actuelle de l'eleve) : un changement de classe "
             "ulterieur (promotion d'annee...) ne doit pas reecrire "
             "l'historique des frais deja factures.")

    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique", required=True)
    academic_term_id = fields.Many2one(
        "op.academic.term", string="Periode")

    fee_type_id = fields.Many2one("op.fee.type", string="Type de frais", required=True)

    date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    amount = fields.Monetary(string="Montant", required=True)
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id)

    journal_id = fields.Many2one(
        "account.journal", string="Journal de facturation", required=True,
        domain=[("type", "=", "sale"), ("school_active", "=", True)],
        default=lambda self: self.env["account.journal"].search(
            [("type", "=", "sale"), ("school_active", "=", True),
             ("company_id", "=", self.env.company.id)], limit=1))

    move_id = fields.Many2one("account.move", string="Facture", readonly=True, copy=False)
    state = fields.Selection(
        [("draft", "Brouillon"), ("posted", "Comptabilise"), ("cancelled", "Annule")],
        default="draft", readonly=True, tracking=True)

    amount_residual = fields.Monetary(
        string="Reste a payer", related="move_id.amount_residual",
        currency_field="currency_id", store=True)
    payment_state = fields.Selection(
        related="move_id.payment_state", string="Statut paiement", store=True)

    bank_receipt_id = fields.Many2one(
        "op.bank.receipt", string="Reçu bancaire",
        domain=[("state", "=", "confirmed")],
        tracking=True,
        help="Reçu bancaire confirmé couvrant ce paiement. Obligatoire avant "
             "d'enregistrer un paiement.")
    bank_receipt_amount_remaining = fields.Monetary(
        string="Solde disponible sur le reçu",
        related="bank_receipt_id.amount_remaining",
        currency_field="currency_id",
        readonly=True,
    )

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)
    note = fields.Text(string="Note")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("classe_id") and vals.get("student_id"):
                student = self.env["op.student"].browse(vals["student_id"])
                if student.classe_id:
                    vals["classe_id"] = student.classe_id.id
        return super().create(vals_list)

    @api.onchange("student_id")
    def _onchange_student_id(self):
        if self.student_id:
            self.classe_id = self.student_id.classe_id

    @api.onchange("fee_type_id")
    def _onchange_fee_type_id(self):
        if self.fee_type_id:
            self.amount = self.fee_type_id.amount

    def action_post(self):
        for rec in self:
            if rec.state != "draft":
                continue
            if rec.amount <= 0:
                raise UserError(_("Le montant doit etre strictement positif."))
            if not rec.fee_type_id.account_id:
                raise UserError(_("Le type de frais doit avoir un compte de produit."))

            description = rec.fee_type_id.name
            if rec.academic_term_id:
                description = "%s - %s" % (description, rec.academic_term_id.name)

            move = self.env["account.move"].create({
                "move_type": "out_invoice",
                "partner_id": rec.partner_id.id,
                "invoice_date": rec.date,
                "journal_id": rec.journal_id.id,
                "company_id": rec.company_id.id,
                "invoice_line_ids": [(0, 0, {
                    "name": description,
                    "quantity": 1,
                    "price_unit": rec.amount,
                    "account_id": rec.fee_type_id.account_id.id,
                })],
            })
            move.action_post()

            if rec.name == "/":
                rec.name = self.env["ir.sequence"].next_by_code("op.student.fee") or move.name
            rec.move_id = move.id
            rec.state = "posted"

    def action_cancel(self):
        for rec in self:
            if rec.state == "cancelled":
                continue
            if rec.state == "draft":
                rec.state = "cancelled"
                continue
            if rec.move_id:
                if rec.move_id.payment_state != "not_paid":
                    raise UserError(
                        _("Impossible d'annuler : un paiement est deja enregistre sur la facture. "
                          "Annulez d'abord le paiement."))
                rec.move_id.button_cancel()
            rec.state = "cancelled"

    def action_register_payment(self):
        self.ensure_one()
        if not self.move_id:
            raise UserError(_("Aucune facture associee a ce frais."))
        if not self.bank_receipt_id:
            raise UserError(_(
                "Vous devez associer un reçu bancaire confirmé avant d'enregistrer "
                "le paiement.\nCréez d'abord un reçu via Finances > Reçus bancaires."))
        available = self.bank_receipt_id.amount_remaining
        if available <= 0:
            raise UserError(_(
                "Le reçu bancaire %(rec)s est épuisé (solde : 0 F).\n"
                "Associez un autre reçu bancaire confirmé.",
                rec=self.bank_receipt_id.name))
        return {
            "type": "ir.actions.act_window",
            "name": _("Enregistrer un paiement"),
            "res_model": "account.payment.register",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_model": "account.move",
                "active_ids": [self.move_id.id],
                "dont_redirect_to_payments": True,
            },
        }

    def action_view_invoice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": self.move_id.id,
            "target": "current",
        }

    def _get_last_payment(self):
        """Retourne le paiement le plus recent lie a la facture de ce frais."""
        if not self.move_id:
            return self.env['account.payment']
        payments = self.move_id._get_reconciled_payments()
        return payments[-1] if payments else self.env['account.payment']

    def action_print_receipt(self):
        self.ensure_one()
        title = "%s — Reçu %s (%s)" % (
            self.env.company.name, self.student_id.name, self.name)
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_op_student_fee_receipt", self, title=title)

    def _get_recap_lines(self):
        """Recapitulatif de tous les frais comptabilises de l'eleve pour
        l'annee academique de ce frais (une ligne par tranche/type de frais)."""
        self.ensure_one()
        fees = self.search([
            ("student_id", "=", self.student_id.id),
            ("academic_year_id", "=", self.academic_year_id.id),
            ("state", "=", "posted"),
        ], order="academic_term_id, fee_type_id")
        lines = []
        for fee in fees:
            if fee.academic_term_id:
                label = "%s : %s" % (fee.fee_type_id.name, fee.academic_term_id.name)
            else:
                label = "Inscription : %s" % fee.fee_type_id.name
            lines.append({
                "label": label,
                "date": fee.date,
                "tarif": fee.amount,
                "paye": fee.amount - fee.amount_residual,
                "reste": fee.amount_residual,
            })
        return lines

    @api.model
    def _amount_to_words(self, amount):
        """Montant en toutes lettres, en francais (ex: 'trente mille francs CFA')."""
        if num2words is None:
            return "%s francs CFA" % "{:,.0f}".format(amount).replace(",", " ")
        try:
            words = num2words(int(round(amount)), lang="fr")
        except Exception:
            words = "{:,.0f}".format(amount).replace(",", " ")
        return "%s francs CFA" % words

    def _get_qr_code_b64(self):
        """QR code encodant la reference du recu, ou False si la librairie
        Python 'qrcode' n'est pas installee sur le serveur."""
        self.ensure_one()
        if qrcode is None:
            return False
        try:
            img = qrcode.make(self.name)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()
        except Exception:
            return False
