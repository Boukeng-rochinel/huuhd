# -*- coding: utf-8 -*-
import base64
import io

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

STAFF_TYPE_LABELS = {
    "non_enseignant": "Non enseignant",
    "enseignant_permanent": "Enseignant permanent",
    "enseignant_vacataire": "Enseignant vacataire",
}


class OpEmployeeListWizard(models.TransientModel):
    _name = "op.employee.list.wizard"
    _description = "Liste du personnel (impression / export)"

    department_id = fields.Many2one("hr.department", string="Departement")
    staff_type = fields.Selection(
        [("tous", "Tous")] + list(STAFF_TYPE_LABELS.items()),
        string="Type de personnel", default="tous", required=True)
    include_archived = fields.Boolean(string="Inclure les archives")

    file_data = fields.Binary(string="Fichier", readonly=True)
    file_name = fields.Char(string="Nom du fichier", readonly=True)

    preview_employee_ids = fields.Many2many(
        "hr.employee", compute="_compute_preview", string="Apercu")
    preview_count = fields.Integer(compute="_compute_preview", string="Nombre d'employes")

    @api.depends("department_id", "staff_type", "include_archived")
    def _compute_preview(self):
        for wizard in self:
            employees = wizard._get_employees()
            wizard.preview_employee_ids = employees
            wizard.preview_count = len(employees)

    # ------------------------------------------------------------------
    # Selection du personnel selon les filtres
    # ------------------------------------------------------------------
    def _get_employees(self):
        self.ensure_one()
        domain = []
        if self.department_id:
            domain.append(("department_id", "=", self.department_id.id))
        if self.staff_type != "tous":
            domain.append(("staff_type", "=", self.staff_type))
        employees = self.env["hr.employee"]
        if self.include_archived:
            employees = employees.with_context(active_test=False)
        return employees.search(domain, order="name")

    # ------------------------------------------------------------------
    # Impression PDF
    # ------------------------------------------------------------------
    def action_print_pdf(self):
        self.ensure_one()
        if not self._get_employees():
            raise UserError(_("Aucun employe ne correspond a ces criteres."))
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_op_employee_list", self)

    # ------------------------------------------------------------------
    # Export Excel
    # ------------------------------------------------------------------
    def action_export_xlsx(self):
        self.ensure_one()
        if xlsxwriter is None:
            raise UserError(
                _("La librairie Python 'xlsxwriter' n'est pas installee "
                  "sur le serveur (pip install xlsxwriter).")
            )
        employees = self._get_employees()
        if not employees:
            raise UserError(_("Aucun employe ne correspond a ces criteres."))

        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = book.add_worksheet(_("Personnel"))

        f_title = book.add_format({"bold": True, "font_size": 14})
        f_head = book.add_format({
            "bold": True, "bg_color": "#714B67", "font_color": "#FFFFFF",
            "border": 1, "align": "center", "valign": "vcenter",
        })
        f_cell = book.add_format({"border": 1})
        f_date = book.add_format({"border": 1, "num_format": "dd/mm/yyyy"})

        headers = [_("Matricule"), _("Nom"), _("Fonction"), _("Departement"),
                   _("Grade"), _("Type de personnel"), _("Date d'embauche")]
        sheet.write(0, 0, _("Liste du personnel"), f_title)
        start = 2
        for c, label in enumerate(headers):
            sheet.set_column(c, c, 24)
            sheet.write(start, c, label, f_head)

        r = start + 1
        for employee in employees:
            sheet.write(r, 0, employee.matricule or "", f_cell)
            sheet.write(r, 1, employee.name or "", f_cell)
            sheet.write(r, 2, employee.job_title or "", f_cell)
            sheet.write(r, 3, employee.department_id.name or "", f_cell)
            sheet.write(r, 4, employee.grade or "", f_cell)
            sheet.write(r, 5, STAFF_TYPE_LABELS.get(employee.staff_type, ""), f_cell)
            if employee.date_embauche:
                sheet.write_datetime(r, 6, employee.date_embauche, f_date)
            else:
                sheet.write(r, 6, "", f_cell)
            r += 1
        sheet.freeze_panes(start + 1, 0)
        book.close()
        output.seek(0)

        fname = "Liste_personnel_%s.xlsx" % fields.Date.today().strftime("%Y%m%d")
        self.write({
            "file_data": base64.b64encode(output.read()),
            "file_name": fname,
        })
        output.close()

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s/%s/file_data/%s?download=true"
                   % (self._name, self.id, self.file_name),
            "target": "self",
        }
