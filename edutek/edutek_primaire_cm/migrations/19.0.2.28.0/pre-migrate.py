# -*- coding: utf-8 -*-
"""Ajoute la colonne school_po_box sur res_company si elle n'existe pas.
Ce champ a ete ajoute au modele mais la colonne manquait sur les instances
existantes, provoquant des erreurs lors des acces a res_company (ex: cron
de planification stock)."""


def migrate(cr, version):
    cr.execute("""
        ALTER TABLE res_company
        ADD COLUMN IF NOT EXISTS school_po_box VARCHAR
    """)
