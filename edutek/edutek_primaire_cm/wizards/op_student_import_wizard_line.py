# -*- coding: utf-8 -*-
from odoo import fields, models


class OpStudentImportWizardLine(models.TransientModel):
    _name = "op.student.import.wizard.line"
    _description = "Ligne d'apercu - import des eleves"
    _order = "row_index"

    wizard_id = fields.Many2one(
        "op.student.import.wizard", required=True, ondelete="cascade")
    row_index = fields.Integer(string="Ligne Excel", readonly=True)

    matricule = fields.Char(string="Matricule", required=True)
    last_name = fields.Char(string="Nom")
    first_name = fields.Char(string="Prenom")
    gender = fields.Selection([("m", "M"), ("f", "F")], string="Sexe")
    birth_date = fields.Date(string="Date de naissance")
    birth_place = fields.Char(string="Lieu de naissance")
    ecole_origine = fields.Char(string="Ecole d'origine")

    est_inscrit = fields.Boolean(string="Est inscrit")
    classe_id = fields.Many2one("op.classe", string="Salle de classe")
    classe_texte = fields.Char(string="Salle de classe (fichier)", readonly=True)
    classe_auto_created = fields.Boolean(string="Classe creee auto.", readonly=True)

    reduction = fields.Float(string="Reduction accordee")
    date_inscription = fields.Date(string="Date d'inscription")
    montant_paye = fields.Float(string="Montant deja paye")

    warning = fields.Char(string="Avertissement", readonly=True)
