# -*- coding: utf-8 -*-
{
    "name": "EduTek - Ecole Complete (Cameroun)",
    "version": "19.0.1.0.0",
    "author": "Custom",
    "category": "Education",
    "summary": "Structure scolaire camerounaise complete : Maternelle, Primaire "
               "et Secondaire, sans creation automatique de classes",
    "description": (
        "Configure la structure de base d'une ecole camerounaise complete "
        "(Maternelle PS-GS, Primaire SIL-CM2, Secondaire francophone "
        "6eme-Terminale et anglophone Form1-Upper Sixth) : annee academique, "
        "3 trimestres de 2 sequences, toutes les matieres et types de frais "
        "standards. Aucune classe n'est creee automatiquement : "
        "l'administrateur cree les classes depuis Configuration > "
        "Fiche de l'ecole > Structures, ou les importe via le wizard "
        "d'importation d'eleves."
    ),
    "depends": ["edutek_maternelle_cm", "edutek_secondaire_cm", "edutek_management_cm"],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
