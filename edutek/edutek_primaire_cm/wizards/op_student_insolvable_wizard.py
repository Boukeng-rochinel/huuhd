# -*- coding: utf-8 -*-
import base64
import io

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class OpStudentInsolvableWizard(models.TransientModel):
    _name = "op.student.insolvable.wizard"
    _description = "Etat des insolvables (frais impayes)"

    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        default=lambda self: self.env.user.current_academic_year_id,
        required=True)
    classe_ids = fields.Many2many(
        "op.classe", string="Classes",
        domain="[('academic_year_id', '=', academic_year_id)]",
        help="Laisser vide pour inclure toutes les classes de l'annee academique.")
    scope = fields.Selection(
        [
            ("annee", "Toute l'annee"),
            ("cumul", "Cumul jusqu'a une periode"),
            ("trimestre", "Une seule periode"),
        ],
        string="Portee", default="annee", required=True)
    academic_term_id = fields.Many2one(
        "op.academic.term", string="Periode",
        domain="[('academic_year_id', '=', academic_year_id)]")
    montant_seuil = fields.Monetary(
        string="Reste a payer minimum",
        help="Si renseigne, ne retient que les eleves dont le reste a "
             "payer est superieur ou egal a ce montant.")
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id)

    file_data = fields.Binary(string="Fichier", readonly=True)
    file_name = fields.Char(string="Nom du fichier", readonly=True)

    preview_html = fields.Html(string="Apercu", compute="_compute_preview", sanitize=False)
    preview_count = fields.Integer(string="Nombre d'eleves", compute="_compute_preview")

    @api.depends("academic_year_id", "classe_ids", "scope", "academic_term_id", "montant_seuil")
    def _compute_preview(self):
        for wizard in self:
            try:
                lines = wizard._get_insolvable_lines() if wizard.academic_year_id else []
            except UserError:
                lines = []
            wizard.preview_count = len(lines)
            wizard.preview_html = wizard._render_preview_html(lines)

    def _render_preview_html(self, lines):
        if not lines:
            return Markup("<p class='text-muted'>Aucun eleve insolvable ne correspond a ces criteres.</p>")

        def fmt(value):
            return "{:,.0f}".format(value).replace(",", " ")

        rows = []
        current_classe = None
        for line in lines:
            classe = line["classe"]
            if classe != current_classe:
                current_classe = classe
                rows.append(Markup(
                    "<tr style='background:#eee;'><td colspan='4'><strong>{}</strong></td></tr>"
                ).format(current_classe.display_name or "Sans classe"))
            rows.append(Markup(
                "<tr><td>{}</td><td>{}</td><td style='text-align:right;'>{}</td>"
                "<td style='text-align:right;'>{}</td></tr>"
            ).format(
                line["matricule"] or "", line["student"].name,
                fmt(line["montant_du"]), fmt(line["reste"])))
        return Markup(
            "<table class='table table-sm table-bordered'>"
            "<thead><tr><th>Matricule</th><th>Nom</th>"
            "<th style='text-align:right;'>Montant du</th>"
            "<th style='text-align:right;'>Reste</th></tr></thead>"
            "<tbody>{}</tbody></table>"
        ).format(Markup("").join(rows))

    # ------------------------------------------------------------------
    # Construction du domaine et agregation par eleve
    # ------------------------------------------------------------------
    def _get_fee_domain(self):
        self.ensure_one()
        if self.scope != "annee" and not self.academic_term_id:
            raise UserError(_("Veuillez selectionner une periode pour cette portee."))

        domain = [
            ("state", "=", "posted"),
            ("academic_year_id", "=", self.academic_year_id.id),
        ]
        if self.classe_ids:
            domain.append(("classe_id", "in", self.classe_ids.ids))
        if self.scope == "trimestre":
            domain.append(("academic_term_id", "=", self.academic_term_id.id))
        elif self.scope == "cumul":
            terms = self.env["op.academic.term"].search([
                ("academic_year_id", "=", self.academic_year_id.id),
                ("term_start_date", "<=", self.academic_term_id.term_start_date),
            ])
            domain.append(("academic_term_id", "in", terms.ids))
        return domain

    def _get_insolvable_lines(self):
        self.ensure_one()
        Fee = self.env["op.student.fee"]
        grouped = Fee._read_group(
            self._get_fee_domain(),
            groupby=["student_id"],
            aggregates=["amount:sum", "amount_residual:sum"])

        students = self.env["op.student"]
        for student, _montant_du, _reste in grouped:
            students |= student
        # La classe courante de l'eleve peut differer de sa classe au cours
        # de l'annee academique consultee (ex: annee precedente) : on
        # privilegie l'historique d'inscription quand il existe.
        history = self.env["op.student.enrollment.history"].search([
            ("student_id", "in", students.ids),
            ("academic_year_id", "=", self.academic_year_id.id),
        ])
        classe_by_student = {h.student_id.id: h.classe_id for h in history}

        lines = []
        for student, montant_du, reste in grouped:
            if reste <= 0:
                continue
            if self.montant_seuil and reste < self.montant_seuil:
                continue
            lines.append({
                "student": student,
                "classe": classe_by_student.get(student.id, student.classe_id),
                "matricule": student.gr_no or "",
                "montant_du": montant_du,
                "montant_verse": montant_du - reste,
                "reste": reste,
            })
        lines.sort(key=lambda line: (line["classe"].display_name or "", line["student"].name or ""))
        return lines

    # ------------------------------------------------------------------
    # Impression PDF
    # ------------------------------------------------------------------
    def action_print_pdf(self):
        self.ensure_one()
        if not self._get_insolvable_lines():
            raise UserError(_("Aucun eleve insolvable ne correspond a ces criteres."))
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_op_student_insolvable", self)

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
        lines = self._get_insolvable_lines()
        if not lines:
            raise UserError(_("Aucun eleve insolvable ne correspond a ces criteres."))

        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = book.add_worksheet(_("Insolvables"))

        f_title = book.add_format({"bold": True, "font_size": 14})
        f_classe = book.add_format({"bold": True, "bg_color": "#EEEEEE"})
        f_head = book.add_format({
            "bold": True, "bg_color": "#714B67", "font_color": "#FFFFFF",
            "border": 1, "align": "center", "valign": "vcenter",
        })
        f_cell = book.add_format({"border": 1})
        f_money = book.add_format({"border": 1, "num_format": "#,##0"})
        f_tot_lbl = book.add_format({"bold": True, "border": 1, "align": "right"})
        f_tot_money = book.add_format(
            {"bold": True, "border": 1, "num_format": "#,##0"})

        sheet.write(0, 0, _("Etat des insolvables"), f_title)
        cols = [
            (_("Matricule"), 14), (_("Nom de l'eleve"), 30),
            (_("Montant du"), 16), (_("Montant verse"), 16), (_("Reste"), 16),
        ]
        for c, (label, width) in enumerate(cols):
            sheet.set_column(c, c, width)

        r = 2
        current_classe = None
        total_du = total_verse = total_reste = 0.0
        for line in lines:
            if line["classe"] != current_classe:
                current_classe = line["classe"]
                sheet.write(r, 0, current_classe.display_name or _("Sans classe"), f_classe)
                r += 1
                for c, (label, _w) in enumerate(cols):
                    sheet.write(r, c, label, f_head)
                r += 1
            sheet.write(r, 0, line["matricule"], f_cell)
            sheet.write(r, 1, line["student"].name, f_cell)
            sheet.write_number(r, 2, line["montant_du"], f_money)
            sheet.write_number(r, 3, line["montant_verse"], f_money)
            sheet.write_number(r, 4, line["reste"], f_money)
            total_du += line["montant_du"]
            total_verse += line["montant_verse"]
            total_reste += line["reste"]
            r += 1

        r += 1
        sheet.write(r, 1, _("TOTAL GENERAL"), f_tot_lbl)
        sheet.write_number(r, 2, total_du, f_tot_money)
        sheet.write_number(r, 3, total_verse, f_tot_money)
        sheet.write_number(r, 4, total_reste, f_tot_money)

        book.close()
        output.seek(0)

        fname = "Etat_insolvables_%s.xlsx" % self.academic_year_id.name.replace("/", "-")
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
