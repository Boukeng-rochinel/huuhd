# -*- coding: utf-8 -*-
from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    sis_pin = fields.Char(
        string="Code PIN EduTek",
        size=6,
        groups="hr.group_hr_manager,base.group_system",
        help="Code PIN pour deverrouiller l'ecran EduTek (4 a 6 chiffres).",
    )
    sis_role = fields.Selection([
        ("admin", "Administrateur"),
        ("teacher", "Enseignant"),
        ("secretary", "Secretaire"),
    ], string="Role EduTek", default="teacher",
       help="Determine ce que cet employe peut voir et faire dans EduTek apres "
            "s'etre authentifie via son PIN. Administrateur : acces complet. "
            "Enseignant : uniquement ses classes et leurs eleves/notes. "
            "Secretaire : eleves et frais, pas la configuration.")

    @api.model
    def get_sis_lock_employees(self):
        """Retourne la liste des employes actifs pour l'ecran de verrouillage."""
        employees = self.sudo().search([('active', '=', True)], order='name asc')
        return [{'id': e.id, 'name': e.name, 'role': e.sis_role or 'teacher'} for e in employees]

    @api.model
    def check_employee_sis_pin(self, employee_id, pin):
        """Valide le PIN EduTek. Retourne les infos de l'employe authentifie,
        ou False si le code est incorrect."""
        employee = self.sudo().browse(employee_id)
        if not employee.exists():
            return False
        ok = (not employee.sis_pin) or (employee.sis_pin == pin)
        if not ok:
            return False
        return {
            'ok': True,
            'id': employee.id,
            'name': employee.name,
            'role': employee.sis_role or 'teacher',
        }

    @api.model
    def get_sis_root_menu_id(self):
        """ID (DB) du menu racine 'EduTek', utilise par le frontend pour detecter
        l'entree dans l'application et y afficher l'ecran de verrouillage."""
        menu = self.env.ref('edutek_core.menu_op_school_root', raise_if_not_found=False)
        return menu.id if menu else False
