# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OpStudentFeeGenerateWizard(models.TransientModel):
    _name = "op.student.fee.generate.wizard"
    _description = "Generer des frais en masse"

    cycle = fields.Selection(
        selection="_selection_cycle", string="Cycle",
        help="Limite la generation aux classes de ce cycle (Maternelle, "
             "Primaire...). Utile pour generer les frais de toute l'ecole "
             "en plusieurs lots plus rapides plutot qu'en une seule fois, "
             "qui peut echouer par timeout sur un grand effectif.")
    classe_ids = fields.Many2many(
        "op.classe", string="Classes",
        domain="[('academic_year_id', '=', academic_year_id)] if not cycle else "
               "[('academic_year_id', '=', academic_year_id), ('cycle', '=', cycle)]",
        help="Laisser vide pour appliquer ce frais a TOUTES les classes de "
             "l'annee academique (ou du cycle choisi ci-dessus si renseigne), "
             "ex: frais d'inscription pour toute l'ecole.")
    fee_type_ids = fields.Many2many(
        "op.fee.type", string="Types de frais", required=True,
        help="Le montant facture a chaque eleve est celui configure pour ce "
             "type de frais sur SA classe (Configuration > Fiche de l'ecole "
             "> Classe), ou le montant par defaut du type de frais si la "
             "classe n'a pas sa propre ligne. Une classe sans aucun montant "
             "configure (0) pour un type choisi est ignoree pour ce type.")
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique", required=True)
    academic_term_id = fields.Many2one(
        "op.academic.term", string="Periode",
        domain="[('academic_year_id', '=', academic_year_id)]")
    date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    journal_id = fields.Many2one(
        "account.journal", string="Journal de facturation", required=True,
        domain=[("type", "=", "sale"), ("school_active", "=", True)],
        default=lambda self: self.env["account.journal"].search(
            [("type", "=", "sale"), ("school_active", "=", True),
             ("company_id", "=", self.env.company.id)], limit=1))
    post_immediately = fields.Boolean(
        string="Comptabiliser immediatement", default=True,
        help="Si coche, les frais generes sont aussitot factures et "
             "comptabilises (comme un clic sur 'Comptabiliser' pour chacun).")

    def _selection_cycle(self):
        return self.env["op.classe"]._selection_cycle()

    def _get_classes(self):
        self.ensure_one()
        if self.classe_ids:
            return self.classe_ids
        domain = [("academic_year_id", "=", self.academic_year_id.id)]
        if self.cycle:
            domain.append(("cycle", "=", self.cycle))
        return self.env["op.classe"].search(domain)

    def _classe_amount(self, classe, fee_type):
        """Montant configure pour ce type de frais sur cette classe
        (Configuration > Fiche de l'ecole > Classe), ou le montant par
        defaut du type de frais si la classe n'a pas sa propre ligne."""
        line = classe.fee_line_ids.filtered(lambda l: l.fee_type_id == fee_type)
        if line and line[0].amount > 0:
            return line[0].amount
        return fee_type.amount

    def action_generate(self):
        self.ensure_one()
        if not self.fee_type_ids:
            raise UserError(_("Veuillez choisir au moins un type de frais."))
        classes = self._get_classes()
        if not classes:
            raise UserError(_("Aucune classe trouvee pour ces criteres."))

        Fee = self.env["op.student.fee"]
        fees = Fee
        skipped_classes = 0
        for classe in classes:
            if (self.academic_term_id
                    and self.academic_term_id not in classe._get_applicable_terms()):
                skipped_classes += 1
                continue
            for fee_type in self.fee_type_ids:
                amount = self._classe_amount(classe, fee_type)
                if amount <= 0:
                    continue
                for student in classe.student_ids:
                    existing = Fee.search([
                        ("student_id", "=", student.id),
                        ("fee_type_id", "=", fee_type.id),
                        ("academic_year_id", "=", self.academic_year_id.id),
                        ("academic_term_id", "=", self.academic_term_id.id),
                    ], limit=1)
                    if not existing:
                        existing = Fee.create({
                            "student_id": student.id,
                            "fee_type_id": fee_type.id,
                            "academic_year_id": self.academic_year_id.id,
                            "academic_term_id": self.academic_term_id.id,
                            "date": self.date,
                            "amount": max(amount - student.discount_amount, 0.0),
                            "journal_id": self.journal_id.id,
                        })
                    fees |= existing

        if self.post_immediately:
            fees.filtered(lambda f: f.state == "draft").action_post()

        name = _("Frais des eleves")
        if skipped_classes:
            name = _(
                "Frais des eleves (%(classes)s classe(s) ignoree(s) : "
                "periode non applicable)", classes=skipped_classes)

        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": "op.student.fee",
            "view_mode": "list,form",
            "domain": [("id", "in", fees.ids)],
            "context": {"search_default_group_classe": 1},
        }
