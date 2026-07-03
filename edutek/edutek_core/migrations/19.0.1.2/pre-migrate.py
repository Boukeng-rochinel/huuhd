# -*- coding: utf-8 -*-


def migrate(cr, version):
    """op.academic.term n'a plus de contrainte d'unicite sur les dates depuis
    l'introduction de la hierarchie Trimestre/Sequence : un Trimestre
    partage deliberement sa date de debut avec sa 1ere Sequence et sa date
    de fin avec sa derniere (cf. commentaire dans op_academic_term.py).
    Odoo n'enleve jamais automatiquement une contrainte SQL retiree du
    modele Python - il faut la supprimer explicitement ici, avant que les
    donnees (backfill_trimestre_grouping) ne soient (re)chargees."""
    cr.execute("""
        ALTER TABLE op_academic_term
        DROP CONSTRAINT IF EXISTS op_academic_term_unique_start_date
    """)
    cr.execute("""
        ALTER TABLE op_academic_term
        DROP CONSTRAINT IF EXISTS op_academic_term_unique_end_date
    """)
