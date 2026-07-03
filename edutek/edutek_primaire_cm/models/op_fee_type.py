# -*- coding: utf-8 -*-
from odoo import api, fields, models

DEFAULT_FEE_TYPES = [
    {"name": "Inscription Scolarite", "code": "INSCRIPTION",
     "is_registration_fee": True, "sequence": 10},
    {"name": "Premiere Tranche Pension", "code": "PENSION-T1", "sequence": 20},
    {"name": "Deuxieme Tranche Pension", "code": "PENSION-T2", "sequence": 30},
]


class OpFeeType(models.Model):
    _name = "op.fee.type"
    _description = "Type de frais scolaire"
    _order = "sequence, name"

    name = fields.Char(string="Libelle", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    code = fields.Char(string="Code")
    amount = fields.Monetary(string="Montant par defaut", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id)
    account_id = fields.Many2one(
        "account.account", string="Compte de produit", required=True,
        domain=[("account_type", "in", ("income", "income_other"))])
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)
    active = fields.Boolean(default=True)
    is_registration_fee = fields.Boolean(
        string="Frais d'inscription",
        help="Un eleve n'est considere 'Inscrit' que s'il a paye un frais de ce type "
             "pour l'annee academique en cours.")
    is_miscellaneous = fields.Boolean(
        string="Frais divers",
        help="Classe ce type de frais dans la categorie 'Frais divers' sur les "
             "etats de caisse, plutot que dans 'Frais de scolarite'.")
    date_limite = fields.Date(
        string="Date limite / expiration",
        help="Date limite de paiement par defaut pour ce type de frais "
             "(affichee sur les recus). A ajuster chaque annee si besoin. "
             "Laisser vide pour utiliser la date de facturation du frais "
             "comme echeance par defaut.")

    _unique_name_company = models.Constraint(
        "unique(name, company_id)",
        "Ce type de frais existe deja pour cette societe.")

    @api.model
    def _get_or_create_default_fee_types(self):
        """Types de frais standards attendus pour toute societe utilisant ce
        module (Inscription Scolarite, Premiere/Deuxieme Tranche Pension) :
        cree ceux qui manquent encore, montant a 0 (a definir par classe
        depuis Configuration > Fiche de l'ecole > Classe). Sans compte de
        produit disponible (societe sans plan comptable encore installe),
        ne cree rien - sera retente a la prochaine mise a jour du module."""
        company = self.env.company
        names = [d["name"] for d in DEFAULT_FEE_TYPES]
        existing = self.search([("name", "in", names), ("company_id", "=", company.id)])
        missing = [d for d in DEFAULT_FEE_TYPES if d["name"] not in existing.mapped("name")]
        if not missing:
            return existing
        income_account = self.env["account.account"].search([
            ("account_type", "in", ("income", "income_other")),
            ("company_ids", "in", company.id),
        ], limit=1)
        if not income_account:
            return existing
        created = self.create([
            {**d, "account_id": income_account.id, "company_id": company.id}
            for d in missing
        ])
        return existing | created
