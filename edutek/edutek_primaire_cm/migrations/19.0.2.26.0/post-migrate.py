# -*- coding: utf-8 -*-
"""op.fee.type passe d'un tri alphabetique (_order = "name") a un tri par
sequence editable/glissable. Sans backfill, tous les types de frais
existants partageraient la meme sequence par defaut (10) et retomberaient
sur l'ancien tri alphabetique comme cle secondaire - ce qui laisserait
"Deuxieme Tranche Pension" avant "Premiere Tranche Pension", l'inverse de
l'ordre logique attendu."""

SEQUENCE_BY_NAME = {
    "Inscription Scolarite": 10,
    "Premiere Tranche Pension": 20,
    "Deuxieme Tranche Pension": 30,
}


def migrate(cr, version):
    cr.execute("SELECT 1 FROM information_schema.columns "
               "WHERE table_name = 'op_fee_type' AND column_name = 'sequence'")
    if not cr.fetchone():
        return
    for name, sequence in SEQUENCE_BY_NAME.items():
        cr.execute(
            "UPDATE op_fee_type SET sequence = %s WHERE name = %s",
            (sequence, name),
        )
