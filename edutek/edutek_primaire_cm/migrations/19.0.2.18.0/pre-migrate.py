# -*- coding: utf-8 -*-
"""hr_employee.staff_type passe de Selection a Many2one(op.staff.type), et
hr_employee.grade de Char a Many2one(op.grade). Odoo va creer les nouvelles
colonnes (type integer) sous les memes noms de champ ; il faut donc liberer
ces noms de colonne *avant* que le registre ne soit recharge, sinon les
anciennes valeurs texte sont perdues. On les met simplement de cote sous un
nom temporaire ; post-migrate.py les relit pour peupler les nouvelles
relations puis les supprime.

Idempotent : si une tentative precedente a deja renomme une colonne (ex:
mise a jour interrompue), on ne la renomme pas une seconde fois.
"""


def _stash_old_column(cr, table, column, tmp_column, expected_pg_type):
    cr.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = %s AND column_name = %s",
        (table, tmp_column))
    if cr.fetchone():
        return  # deja mis de cote par une tentative precedente

    cr.execute(
        "SELECT data_type FROM information_schema.columns "
        "WHERE table_name = %s AND column_name = %s",
        (table, column))
    row = cr.fetchone()
    if row and row[0] == expected_pg_type:
        cr.execute(
            'ALTER TABLE "%s" RENAME COLUMN "%s" TO "%s"'
            % (table, column, tmp_column))


def migrate(cr, version):
    _stash_old_column(cr, "hr_employee", "staff_type", "staff_type_old_text", "character varying")
    _stash_old_column(cr, "hr_employee", "grade", "grade_old_text", "character varying")
