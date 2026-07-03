# -*- coding: utf-8 -*-
import base64
import io

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class OpClasseListWizard(models.TransientModel):
    _name = "op.classe.list.wizard"
    _description = "Liste des classes (impression / export)"

    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        default=lambda self: self.env.user.current_academic_year_id)
    level = fields.Selection(selection="_selection_level", string="Niveau")
    cycle = fields.Selection(selection="_selection_cycle", string="Cycle")
    teacher_id = fields.Many2one("hr.employee", string="Enseignant")
    created_by_id = fields.Many2one("res.users", string="Cree par")

    file_data = fields.Binary(string="Fichier", readonly=True)
    file_name = fields.Char(string="Nom du fichier", readonly=True)

    preview_classe_ids = fields.Many2many(
        "op.classe", compute="_compute_preview", string="Apercu")
    preview_count = fields.Integer(compute="_compute_preview", string="Nombre de classes")

    def _selection_level(self):
        return self.env["op.classe"]._selection_level()

    def _selection_cycle(self):
        return self.env["op.classe"]._selection_cycle()

    @api.depends("academic_year_id", "level", "cycle", "teacher_id", "created_by_id")
    def _compute_preview(self):
        for wizard in self:
            classes = wizard._get_classes()
            wizard.preview_classe_ids = classes
            wizard.preview_count = len(classes)

    # ------------------------------------------------------------------
    # Selection des classes selon les filtres
    # ------------------------------------------------------------------
    def _get_classes(self):
        self.ensure_one()
        domain = []
        if self.academic_year_id:
            domain.append(("academic_year_id", "=", self.academic_year_id.id))
        if self.level:
            domain.append(("level", "=", self.level))
        if self.cycle:
            domain.append(("cycle", "=", self.cycle))
        if self.teacher_id:
            domain.append(("teacher_id", "=", self.teacher_id.id))
        if self.created_by_id:
            domain.append(("create_uid", "=", self.created_by_id.id))
        return self.env["op.classe"].with_context(academic_year_all=1).search(
            domain, order="level_order, name")

    # ------------------------------------------------------------------
    # Impression PDF
    # ------------------------------------------------------------------
    def action_print_pdf(self):
        self.ensure_one()
        if not self._get_classes():
            raise UserError(_("Aucune classe ne correspond a ces criteres."))
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_op_classe_list", self)

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
        classes = self._get_classes()
        if not classes:
            raise UserError(_("Aucune classe ne correspond a ces criteres."))

        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = book.add_worksheet(_("Classes"))

        f_title = book.add_format({"bold": True, "font_size": 14})
        f_head = book.add_format({
            "bold": True, "bg_color": "#714B67", "font_color": "#FFFFFF",
            "border": 1, "align": "center", "valign": "vcenter",
        })
        f_cell = book.add_format({"border": 1})
        f_int = book.add_format({"border": 1, "num_format": "0"})

        level_labels = dict(self._selection_level())
        cycle_labels = dict(self._selection_cycle())

        headers = [_("Nom"), _("Niveau"), _("Cycle"), _("Enseignant"), _("Effectif")]
        sheet.write(0, 0, _("Liste des classes"), f_title)
        start = 2
        for c, label in enumerate(headers):
            sheet.set_column(c, c, 24)
            sheet.write(start, c, label, f_head)

        r = start + 1
        for classe in classes:
            sheet.write(r, 0, classe.name or "", f_cell)
            sheet.write(r, 1, level_labels.get(classe.level, classe.level or ""), f_cell)
            sheet.write(r, 2, cycle_labels.get(classe.cycle, classe.cycle or ""), f_cell)
            sheet.write(r, 3, classe.teacher_id.name or "", f_cell)
            sheet.write(r, 4, classe.student_count, f_int)
            r += 1
        sheet.freeze_panes(start + 1, 0)
        book.close()
        output.seek(0)

        fname = "Liste_classes_%s.xlsx" % fields.Date.today().strftime("%Y%m%d")
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
