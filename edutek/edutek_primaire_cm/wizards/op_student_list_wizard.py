# -*- coding: utf-8 -*-
import base64
import io

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

GENDER_LABELS = {"m": "Masculin", "f": "Feminin", "o": "Autre"}


class OpStudentListWizard(models.TransientModel):
    _name = "op.student.list.wizard"
    _description = "Liste des eleves (impression / export)"

    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        default=lambda self: self.env.user.current_academic_year_id)
    classe_ids = fields.Many2many(
        "op.classe", string="Classes",
        domain="[('academic_year_id', '=', academic_year_id)]",
        help="Laisser vide pour inclure toutes les classes de l'annee academique.")
    inscription_state = fields.Selection(
        [("tous", "Tous"), ("inscrit", "Inscrit"), ("non_inscrit", "Non Inscrit")],
        string="Statut d'inscription", default="inscrit", required=True)
    enrollment_type = fields.Selection(
        [("tous", "Tous"), ("ancien", "Ancien"), ("nouveau", "Nouveau")],
        string="Statut eleve", default="tous", required=True)
    list_type = fields.Selection(
        [("simple", "Liste simple"), ("photos", "Liste avec photos")],
        string="Type de liste", default="simple", required=True)

    date_from = fields.Date(string="Inscrit a partir du")
    date_to = fields.Date(string="Inscrit jusqu'au")
    created_by_id = fields.Many2one("res.users", string="Inscrit par")
    teacher_id = fields.Many2one("hr.employee", string="Enseignant (classe)")

    show_matricule = fields.Boolean(string="Matricule", default=True)
    show_classe = fields.Boolean(string="Classe", default=True)
    show_genre = fields.Boolean(string="Genre", default=True)
    show_naissance = fields.Boolean(string="Date de naissance", default=True)
    show_age = fields.Boolean(string="Age", default=True)
    show_lieu_naissance = fields.Boolean(string="Lieu de naissance", default=False)

    file_data = fields.Binary(string="Fichier", readonly=True)
    file_name = fields.Char(string="Nom du fichier", readonly=True)

    preview_student_ids = fields.Many2many(
        "op.student", compute="_compute_preview", string="Apercu")
    preview_count = fields.Integer(compute="_compute_preview", string="Nombre d'eleves")

    @api.depends("academic_year_id", "classe_ids", "inscription_state", "enrollment_type",
                 "date_from", "date_to", "created_by_id", "teacher_id")
    def _compute_preview(self):
        for wizard in self:
            students = wizard._get_students() if wizard.academic_year_id else self.env["op.student"]
            wizard.preview_student_ids = students
            wizard.preview_count = len(students)

    # ------------------------------------------------------------------
    # Selection des eleves selon les filtres
    # ------------------------------------------------------------------
    def _get_students(self):
        self.ensure_one()
        domain = []
        if self.classe_ids:
            domain.append(("classe_id", "in", self.classe_ids.ids))
        elif self.academic_year_id:
            domain.append(("classe_id.academic_year_id", "=", self.academic_year_id.id))
        if self.inscription_state != "tous":
            domain.append(("inscription_state", "=", self.inscription_state))
        if self.enrollment_type != "tous":
            domain.append(("enrollment_type", "=", self.enrollment_type))
        if self.date_from:
            domain.append(("create_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("create_date", "<=", self.date_to))
        if self.created_by_id:
            domain.append(("create_uid", "=", self.created_by_id.id))
        if self.teacher_id:
            domain.append(("classe_id.teacher_id", "=", self.teacher_id.id))
        return self.env["op.student"].with_context(academic_year_all=1).search(
            domain, order="classe_id, name")

    def _get_columns(self):
        self.ensure_one()
        cols = [("name", _("Nom"))]
        if self.show_matricule:
            cols.append(("gr_no", _("Matricule")))
        if self.show_classe:
            cols.append(("classe_id", _("Classe")))
        if self.show_genre:
            cols.append(("gender", _("Genre")))
        if self.show_naissance:
            cols.append(("birth_date", _("Date de naissance")))
        if self.show_age:
            cols.append(("age", _("Age")))
        if self.show_lieu_naissance:
            cols.append(("birth_place", _("Lieu de naissance")))
        return cols

    # ------------------------------------------------------------------
    # Impression PDF
    # ------------------------------------------------------------------
    def action_print_pdf(self):
        self.ensure_one()
        if not self._get_students():
            raise UserError(_("Aucun eleve ne correspond a ces criteres."))
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_op_student_list", self)

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
        students = self._get_students()
        if not students:
            raise UserError(_("Aucun eleve ne correspond a ces criteres."))
        cols = self._get_columns()

        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = book.add_worksheet(_("Eleves"))

        f_title = book.add_format({"bold": True, "font_size": 14})
        f_head = book.add_format({
            "bold": True, "bg_color": "#714B67", "font_color": "#FFFFFF",
            "border": 1, "align": "center", "valign": "vcenter",
        })
        f_cell = book.add_format({"border": 1})
        f_date = book.add_format({"border": 1, "num_format": "dd/mm/yyyy"})

        sheet.write(0, 0, _("Liste des eleves"), f_title)
        start = 2
        for c, (key, label) in enumerate(cols):
            sheet.set_column(c, c, 22)
            sheet.write(start, c, label, f_head)

        r = start + 1
        for student in students:
            for c, (key, label) in enumerate(cols):
                value = student[key]
                if key == "classe_id":
                    sheet.write(r, c, value.display_name if value else "", f_cell)
                elif key == "gender":
                    sheet.write(r, c, GENDER_LABELS.get(value, value or ""), f_cell)
                elif key == "birth_date" and value:
                    sheet.write_datetime(r, c, value, f_date)
                else:
                    sheet.write(r, c, value or "", f_cell)
            r += 1
        sheet.freeze_panes(start + 1, 0)
        book.close()
        output.seek(0)

        fname = "Liste_eleves_%s.xlsx" % fields.Date.today().strftime("%Y%m%d")
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
