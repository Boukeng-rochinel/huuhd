# -*- coding: utf-8 -*-
{
    "name": "EduTek - Ecole Maternelle (Cameroun)",
    "version": "19.0.1.3.0",
    "author": "Custom",
    "category": "Education",
    "summary": "Gestion de la maternelle : evaluation par competences et carnet de suivi",
    "description": "Module complementaire a edutek_primaire_cm pour la maternelle "
                    "camerounaise (Petite, Moyenne et Grande Section) : evaluation par "
                    "competences (acquis / en cours d'acquisition / non acquis) et "
                    "carnet de suivi trimestriel, remplacant les notes /20 et le bulletin.",
    "depends": ["edutek_primaire_cm"],
    "data": [
        "security/ir.model.access.csv",
        "data/op_education_structure_data.xml",
        "views/op_classe_views.xml",
        "views/op_student_skill_views.xml",
        "views/op_carnet_views.xml",
        "views/menu_restructure.xml",
        "report/op_carnet_report.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
    "license": "LGPL-3",
}
