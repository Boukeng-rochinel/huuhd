# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import AccessError

SCHOOL_INFO_FIELDS = (
    "name", "logo", "phone", "email", "school_po_box", "school_motto", "school_motto_en",
    "delegation_regionale", "delegation_departementale", "school_authorization",
    "certificate_background", "certificate_background_filename",
)

MATRICULE_SEQUENCE_CODE = "op.student.gr_no"


class ResCompany(models.Model):
    _inherit = "res.company"

    delegation_regionale = fields.Char(
        string="Delegation regionale",
        help="Ex: DELEGATION REGIONALE DU LITTORAL. Affiche sur les "
             "certificats, attestations et autres documents officiels.")
    delegation_departementale = fields.Char(
        string="Delegation departementale",
        help="Ex: DELEGATION DEPARTEMENTALE DU WOURI. Affiche sur les "
             "certificats, attestations et autres documents officiels.")
    school_po_box = fields.Char(
        string="Boite postale (BP)",
        help="Ex: BP 1234. Affiche dans les coordonnees de l'ecole sur les "
             "documents officiels.")
    school_authorization = fields.Char(
        string="Autorisation",
        help="Numero/reference de l'autorisation d'ouverture ou de "
             "fonctionnement de l'etablissement. Affiche sur les "
             "certificats, attestations et autres documents officiels.")
    school_motto = fields.Char(
        string="Devise de l'ecole (FR)",
        help="Ex: Discipline - Travail - Reussite. Affiche sous le nom de "
             "l'ecole sur les documents officiels.")
    school_motto_en = fields.Char(
        string="Devise de l'ecole (EN)",
        help="Ex: Discipline - Hardwork - Success. Utilisee sur les documents "
             "generes pour les classes anglophones. Si vide, la devise FR est "
             "reutilisee telle quelle.")
    matricule_auto_assign = fields.Boolean(
        string="Generer automatiquement le matricule", default=True,
        help="Si coche, un matricule (prefixe + numero de sequence) est "
             "attribue automatiquement a tout nouvel eleve qui n'en a pas "
             "deja un.")
    matricule_default_prefix = fields.Char(
        string="Prefixe par defaut du matricule",
        help="Utilise pour les eleves dont la classe n'a pas son propre "
             "prefixe de matricule (Configuration > Fiche de l'ecole > "
             "Classe). Le numero de sequence reste commun a toute "
             "l'ecole, seul le prefixe change.")
    certificate_background = fields.Binary(
        string="Modele de fond pour les certificats",
        help="Image de fond pleine page (format paysage) utilisee a la "
             "place du cadre decoratif par defaut sur les certificats de "
             "promotion. Laisser vide pour garder le cadre genere "
             "automatiquement.")
    certificate_background_filename = fields.Char(string="Nom du fichier (fond certificat)")

    def _check_school_config_admin(self):
        if not self.env.user.has_group("edutek_core.group_op_back_office_admin"):
            raise AccessError(_(
                "Seuls les responsables (groupe Manager) peuvent modifier "
                "la fiche de l'ecole."))

    def _matricule_sequence(self):
        return self.env["ir.sequence"].sudo().search(
            [("code", "=", MATRICULE_SEQUENCE_CODE),
             ("company_id", "in", (self.env.company.id, False))], limit=1)

    def _migrate_matricule_prefix(self, sequence):
        """Compat : avant l'ajout du prefixe par classe, le prefixe du
        matricule vivait directement sur la sequence. Le recupere une seule
        fois dans le nouveau champ company puis vide la sequence, pour que
        next_by_code() ne renvoie plus que le numero (le prefixe est
        desormais assemble en Python, classe par classe)."""
        if not self.env.company.matricule_default_prefix and sequence.prefix:
            self.env.company.sudo().matricule_default_prefix = sequence.prefix
            sequence.sudo().prefix = ""

    def _next_matricule(self, classe=False):
        """Construit le prochain matricule : prefixe de la classe (ou
        prefixe par defaut de l'ecole si la classe n'en a pas) + numero
        d'une sequence partagee par toute l'ecole."""
        sequence = self._matricule_sequence()
        self._migrate_matricule_prefix(sequence)
        number = self.env["ir.sequence"].next_by_code(MATRICULE_SEQUENCE_CODE)
        prefix = (classe and classe.matricule_prefix) or self.env.company.matricule_default_prefix or ""
        return "%s%s" % (prefix, number)

    @api.model
    def get_school_info(self):
        company = self.env.company
        return {field: company[field] for field in SCHOOL_INFO_FIELDS}

    @api.model
    def set_school_info(self, vals):
        self._check_school_config_admin()
        allowed_vals = {k: v for k, v in vals.items() if k in SCHOOL_INFO_FIELDS}
        self.env.company.sudo().write(allowed_vals)

    @api.model
    def get_matricule_config(self):
        sequence = self._matricule_sequence()
        if sequence:
            self._migrate_matricule_prefix(sequence)
        return {
            "auto_assign": self.env.company.matricule_auto_assign,
            "prefix": self.env.company.matricule_default_prefix or "",
            "padding": sequence.padding if sequence else 4,
            "number_next": sequence.number_next_actual if sequence else 1,
        }

    @api.model
    def set_matricule_config(self, vals):
        self._check_school_config_admin()
        company_vals = {}
        if "auto_assign" in vals:
            company_vals["matricule_auto_assign"] = bool(vals["auto_assign"])
        if "prefix" in vals:
            company_vals["matricule_default_prefix"] = vals["prefix"] or ""
        if company_vals:
            self.env.company.sudo().write(company_vals)
        sequence = self._matricule_sequence()
        if sequence:
            seq_vals = {}
            if "padding" in vals:
                seq_vals["padding"] = int(vals["padding"]) or 1
            if "number_next" in vals:
                seq_vals["number_next_actual"] = int(vals["number_next"]) or 1
            if seq_vals:
                sequence.write(seq_vals)
