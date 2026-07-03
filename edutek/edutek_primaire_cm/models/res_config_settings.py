# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    use_ex_aequo_ranking = fields.Boolean(
        string="Utiliser les rangs ex-aequo",
        config_parameter="edutek_primaire_cm.use_ex_aequo_ranking",
        default=True,
        help="Les eleves a moyenne egale partagent le meme rang (le rang "
             "suivant tient compte de l'effectif des ex-aequo). Si "
             "decoche, le rang suit simplement l'ordre de classement.")
    show_photo_on_student_card = fields.Boolean(
        string="Inserer la photo de l'eleve sur la carte scolaire",
        config_parameter="edutek_primaire_cm.show_photo_on_student_card",
        default=True)
    school_motto = fields.Char(
        related="company_id.school_motto", string="Devise de l'ecole (FR)", readonly=False)
    school_motto_en = fields.Char(
        related="company_id.school_motto_en", string="Devise de l'ecole (EN)", readonly=False)
    delegation_regionale = fields.Char(
        related="company_id.delegation_regionale", string="Delegation regionale",
        readonly=False)
    delegation_departementale = fields.Char(
        related="company_id.delegation_departementale",
        string="Delegation departementale", readonly=False)
    canon_scan_dir = fields.Char(
        string="Dossier scanner Canon",
        config_parameter="edutek.canon_scan_dir",
        help="Chemin du dossier réseau où le scanner Canon dépose les images "
             "(ex: /mnt/canon_scans/). Le cron EduTek surveille ce dossier "
             "toutes les minutes et crée automatiquement les reçus bancaires.")
