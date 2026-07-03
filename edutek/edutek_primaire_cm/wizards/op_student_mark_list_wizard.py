# -*- coding: utf-8 -*-
import base64
import io

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class OpStudentMarkListWizard(models.TransientModel):
    _name = "op.student.mark.list.wizard"
    _description = "Liste des notes (impression / export)"

    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        default=lambda self: self.env.user.current_academic_year_id)
    classe_ids = fields.Many2many(
        "op.classe", string="Classes",
        domain="[('academic_year_id', '=', academic_year_id)]",
        help="Laisser vide pour inclure toutes les classes de l'annee academique.")
    subject_id = fields.Many2one("op.subject", string="Matiere")
    academic_term_id = fields.Many2one("op.academic.term", string="Periode")
    note_filter = fields.Selection(
        [("tous", "Toutes"), ("insuffisant", "Insuffisantes (< 10)"),
         ("suffisant", "Suffisantes (>= 10)")],
        string="Notes", default="tous", required=True)
    date_from = fields.Date(string="Saisi a partir du")
    date_to = fields.Date(string="Saisi jusqu'au")
    created_by_id = fields.Many2one("res.users", string="Saisi par")
    teacher_id = fields.Many2one("hr.employee", string="Enseignant titulaire")

    file_data = fields.Binary(string="Fichier", readonly=True)
    file_name = fields.Char(string="Nom du fichier", readonly=True)

    preview_mark_ids = fields.Many2many(
        "op.student.mark", compute="_compute_preview", string="Apercu")
    preview_count = fields.Integer(compute="_compute_preview", string="Nombre de notes")

    @api.depends("academic_year_id", "classe_ids", "subject_id", "academic_term_id",
                 "note_filter", "date_from", "date_to", "created_by_id", "teacher_id")
    def _compute_preview(self):
        for wizard in self:
            marks = wizard._get_marks() if wizard.academic_year_id else self.env["op.student.mark"]
            wizard.preview_mark_ids = marks
            wizard.preview_count = len(marks)

    # ------------------------------------------------------------------
    # Selection des notes selon les filtres
    # ------------------------------------------------------------------
    def _get_marks(self):
        self.ensure_one()
        domain = []
        if self.classe_ids:
            domain.append(("classe_id", "in", self.classe_ids.ids))
        elif self.academic_year_id:
            domain.append(("academic_year_id", "=", self.academic_year_id.id))
        if self.subject_id:
            domain.append(("subject_id", "=", self.subject_id.id))
        if self.academic_term_id:
            domain.append(("academic_term_id", "=", self.academic_term_id.id))
        if self.note_filter == "insuffisant":
            domain.append(("note", "<", 10))
        elif self.note_filter == "suffisant":
            domain.append(("note", ">=", 10))
        if self.date_from:
            domain.append(("create_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("create_date", "<=", self.date_to))
        if self.created_by_id:
            domain.append(("create_uid", "=", self.created_by_id.id))
        if self.teacher_id:
            domain.append(("classe_id.teacher_id", "=", self.teacher_id.id))
        return self.env["op.student.mark"].search(
            domain, order="classe_id, student_id, subject_id")

    # ------------------------------------------------------------------
    # Impression PDF
    # ------------------------------------------------------------------
    def action_print_pdf(self):
        self.ensure_one()
        if not self._get_marks():
            raise UserError(_("Aucune note ne correspond a ces criteres."))
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_op_student_mark_list", self)

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
        marks = self._get_marks()
        if not marks:
            raise UserError(_("Aucune note ne correspond a ces criteres."))

        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = book.add_worksheet(_("Notes"))

        f_title = book.add_format({"bold": True, "font_size": 14})
        f_head = book.add_format({
            "bold": True, "bg_color": "#714B67", "font_color": "#FFFFFF",
            "border": 1, "align": "center", "valign": "vcenter",
        })
        f_cell = book.add_format({"border": 1})
        f_num = book.add_format({"border": 1, "num_format": "0.00"})

        headers = [_("Classe"), _("Eleve"), _("Matiere"), _("Periode"),
                   _("Note"), _("Note x Coef")]
        sheet.write(0, 0, _("Liste des notes"), f_title)
        start = 2
        for c, label in enumerate(headers):
            sheet.set_column(c, c, 22)
            sheet.write(start, c, label, f_head)

        r = start + 1
        for mark in marks:
            sheet.write(r, 0, mark.classe_id.display_name or "", f_cell)
            sheet.write(r, 1, mark.student_id.name or "", f_cell)
            sheet.write(r, 2, mark.subject_id.name or "", f_cell)
            sheet.write(r, 3, mark.academic_term_id.display_name or "", f_cell)
            sheet.write(r, 4, mark.note, f_num)
            sheet.write(r, 5, mark.note_x_coef, f_num)
            r += 1
        sheet.freeze_panes(start + 1, 0)
        book.close()
        output.seek(0)

        fname = "Liste_notes_%s.xlsx" % fields.Date.today().strftime("%Y%m%d")
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
