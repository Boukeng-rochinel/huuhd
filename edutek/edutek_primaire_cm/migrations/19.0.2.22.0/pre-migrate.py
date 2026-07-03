# -*- coding: utf-8 -*-


def migrate(cr, version):
    """_unique_gr_no passe de unique(gr_no) (edutek_core) a
    unique(gr_no, academic_year_id) (edutek_primaire_cm) : le matricule est
    l'identite permanente de l'eleve d'une annee a l'autre (carte scolaire,
    dossiers d'examens officiels...), repris tel quel par op.student.
    _clone_for_next_year() lors de la cloture d'annee - il ne doit donc plus
    etre unique que parmi les dossiers d'une meme annee academique.

    Odoo ne remplace jamais une contrainte SQL existante portant le meme nom
    quand sa definition Python change : on la supprime ici, le schema-sync
    habituel la recree juste apres avec la nouvelle definition."""
    cr.execute("""
        ALTER TABLE op_student
        DROP CONSTRAINT IF EXISTS op_student_unique_gr_no
    """)
