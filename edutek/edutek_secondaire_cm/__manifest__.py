# -*- coding: utf-8 -*-
{
    "name": "EduTek - Ecole Secondaire (Cameroun)",
    "version": "19.0.1.2.0",
    "author": "Custom",
    "category": "Education",
    "summary": "Extension secondaire (college / lycee) francophone et anglophone",
    "description": "Module complementaire a edutek_primaire_cm pour le secondaire "
                    "camerounais : niveaux du college et du lycee, sous-systemes "
                    "francophone (6eme a Terminale) et anglophone (Form 1 a Upper Sixth), "
                    "champ serie, et impression du bulletin en anglais pour les classes "
                    "anglophones. Le moteur de notes /20, coefficients, rang et "
                    "appreciation d'edutek_primaire_cm est reutilise sans modification.",
    "depends": ["edutek_primaire_cm"],
    "data": [
        "data/op_education_structure_data.xml",
        "views/op_classe_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "LGPL-3",
}
