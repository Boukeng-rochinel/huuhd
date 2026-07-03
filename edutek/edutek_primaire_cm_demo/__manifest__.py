# -*- coding: utf-8 -*-
{
    "name": "EduTek - Donnees de demo (Ecole Camerounaise complete)",
    "version": "19.0.1.0.1",
    "author": "Custom",
    "category": "Education",
    "summary": "Donnees de demonstration pour toute l'ecole : maternelle, primaire et secondaire",
    "description": "Module installable / desinstallable simulant une ecole camerounaise complete : "
                    "maternelle (PS/MS/GS), primaire (SIL a CM2) et secondaire francophone "
                    "(6eme a Terminale) et anglophone (Form 1 a Upper Sixth), avec 3 sections "
                    "(A/B/C) par niveau. Annee academique, programmes, eleves, notes, "
                    "evaluations par competences (maternelle) et frais scolaires de "
                    "demonstration. La desinstallation supprime toutes ces donnees.",
    "depends": ["edutek_maternelle_cm", "edutek_secondaire_cm"],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
