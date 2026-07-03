# -*- coding: utf-8 -*-
{
    "name": "EduTek - Cameroun System",
    "version": "19.0.1.0.0",
    "author": "Custom",
    "category": "Education",
    "summary": "Structure scolaire camerounaise propre (annee academique en 3 "
               "trimestres de 2 sequences, classes, programmes) sans eleves "
               "de demonstration",
    "description": (
        "Module installable / desinstallable qui met en place la structure de "
        "base d'une ecole camerounaise complete - maternelle (PS/MS/GS), "
        "primaire (SIL a CM2) et secondaire francophone (6eme a Terminale) et "
        "anglophone (Form 1 a Upper Sixth) - selon un decoupage en 3 trimestres "
        "de 2 sequences chacun par annee academique (6 sequences au total) : "
        "annee academique, trimestres/sequences, matieres, types de frais "
        "standards, classes et leurs programmes (matieres / coefficients).\n\n"
        "A la difference d'EduTek - Donnees de demo, ce module NE CREE AUCUN "
        "ELEVE : c'est une structure de depart propre, pas une simulation. "
        "Les classes terminales de chaque cycle (CM2, 3eme, Terminale, "
        "Form 5, Upper Sixth) sont marquees 'classe d'examen' (champ "
        "informatif) : par convention, elles s'arretent a la Sequence 5 - "
        "pour que cela prenne reellement effet sur la saisie des notes et "
        "la generation des bulletins/frais, restreindre les sequences "
        "applicables de la classe concernee (Toutes les classes > onglet "
        "'Periodes', champ ajoute par edutek_primaire_cm).\n\n"
        "La desinstallation supprime toutes ces donnees."
    ),
    "depends": ["edutek_maternelle_cm", "edutek_secondaire_cm"],
    "data": [
        "data/backfill_trimestre_grouping.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
