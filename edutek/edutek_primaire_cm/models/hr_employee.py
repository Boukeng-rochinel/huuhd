# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    title = fields.Many2one("res.partner.title", string="Civilite")
    adresse = fields.Char(string="Adresse")

    staff_type = fields.Many2one(
        "op.staff.type", string="Type de personnel",
        default=lambda self: self.env.ref(
            "edutek_primaire_cm.op_staff_type_non_enseignant", raise_if_not_found=False))

    grade = fields.Many2one("op.grade", string="Grade")
    matricule = fields.Char(string="Matricule")
    diplome = fields.Char(string="Diplome")
    lieu_exercice = fields.Char(string="Lieu d'exercice")
    acte_nomination = fields.Char(string="Nomme/affecte suivant l'acte N")
    arrondissement_origine = fields.Char(string="Arrondissement d'origine")
    departement_origine = fields.Char(string="Departement d'origine")
    region_origine = fields.Char(string="Region d'origine")
    tribu = fields.Char(string="Tribu")

    date_entree_administration = fields.Date(
        string="Date d'entree dans l'administration / fonction publique")
    date_prise_service_annee = fields.Date(
        string="Date de prise de service pour l'annee courante")
    date_embauche = fields.Date(string="Date d'embauche")
    date_depart = fields.Date(string="Date de depart")
    debut_stage = fields.Date(string="Debut de stage")
    fin_stage = fields.Date(string="Fin de stage")
