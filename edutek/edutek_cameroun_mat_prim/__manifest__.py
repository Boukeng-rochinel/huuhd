# -*- coding: utf-8 -*-
{
    "name": "EduTek - Maternelle & Primaire (Cameroun)",
    "version": "19.0.1.0.0",
    "author": "Custom",
    "category": "Education",
    "summary": "Structure scolaire camerounaise Maternelle + Primaire "
               "(PS a CM2) sans creation automatique de classes",
    "description": (
        "Configure la structure de base d'une ecole camerounaise "
        "Maternelle + Primaire : annee academique, 3 trimestres de 2 "
        "sequences, matieres et types de frais standards. "
        "Aucune classe n'est creee automatiquement : l'administrateur "
        "cree les classes manuellement depuis Configuration > "
        "Fiche de l'ecole > Structures."
    ),
    "depends": ["edutek_maternelle_cm", "edutek_primaire_cm", "edutek_management_cm"],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
