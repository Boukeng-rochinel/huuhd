# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class OpClasseFee(models.Model):
    _name = "op.classe.fee"
    _description = "Frais configure pour une classe"
    _order = "sequence, id"

    classe_id = fields.Many2one("op.classe", string="Classe", required=True, ondelete="cascade")
    fee_type_id = fields.Many2one("op.fee.type", string="Type de frais", required=True)
    amount = fields.Monetary(string="Montant", required=True)
    currency_id = fields.Many2one(
        "res.currency", related="classe_id.company_id.currency_id", string="Devise")
    sequence = fields.Integer(string="Sequence", default=10)

    _unique_classe_fee_type = models.Constraint(
        "unique(classe_id, fee_type_id)",
        "Ce type de frais est deja configure pour cette classe.")

    def _generated_student_fees(self):
        """Frais d'eleves deja generes a partir de cette ligne de
        configuration (meme classe, meme type de frais) - quel que soit
        leur etat (un brouillon non encore comptabilise porte deja le
        montant actuel, le modifier ici le rendrait incoherent)."""
        self.ensure_one()
        return self.env["op.student.fee"].search([
            ("classe_id", "=", self.classe_id.id),
            ("fee_type_id", "=", self.fee_type_id.id),
        ], limit=1)

    def write(self, vals):
        if "amount" in vals or "fee_type_id" in vals:
            for rec in self:
                if rec._generated_student_fees():
                    raise UserError(_(
                        "Impossible de modifier ce frais : des frais ont deja "
                        "ete generes pour des eleves de la classe '%(classe)s' "
                        "a partir de cette configuration ('%(fee_type)s'). "
                        "Supprimez d'abord ces frais generes (Finances > Frais "
                        "des eleves) si vous devez vraiment changer le montant "
                        "ou le type.") % {
                        "classe": rec.classe_id.name,
                        "fee_type": rec.fee_type_id.name,
                    })
        return super().write(vals)
