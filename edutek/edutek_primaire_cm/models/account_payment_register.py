# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):
        move_ids = self._context.get("active_ids", [])
        if move_ids:
            fees = self.env["op.student.fee"].search([
                ("move_id", "in", move_ids),
                ("bank_receipt_id", "!=", False),
            ])
            for fee in fees:
                due = fee.amount_residual
                available = fee.bank_receipt_id.amount_remaining

                if self.amount > due + 0.01:
                    raise UserError(_(
                        "Le montant saisi (%(amount)s F) dépasse le restant dû "
                        "sur ce frais (%(due)s F).\n"
                        "Réduisez le montant.",
                        amount="{:,.0f}".format(self.amount).replace(",", " "),
                        due="{:,.0f}".format(due).replace(",", " "),
                    ))

                if self.amount > available + 0.01:
                    raise UserError(_(
                        "Le montant saisi (%(amount)s F) dépasse le solde disponible "
                        "sur le reçu %(name)s.\n"
                        "Disponible : %(avail)s F — Réduisez le montant.",
                        amount="{:,.0f}".format(self.amount).replace(",", " "),
                        name=fee.bank_receipt_id.name,
                        avail="{:,.0f}".format(available).replace(",", " "),
                    ))

        return super().action_create_payments()
