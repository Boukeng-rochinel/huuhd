# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    school_active = fields.Boolean(
        string="Utilise par l'ecole", default=True,
        help="Si decoche, ce journal n'apparait plus dans les listes de "
             "caisses/journaux proposees par les ecrans EduTek (frais, "
             "encaissements...).")
