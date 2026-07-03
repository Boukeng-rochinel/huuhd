# -*- coding: utf-8 -*-
import base64
import io

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

PAYMENT_STATE_LABELS = {"not_paid": "Non paye", "partial": "Partiel", "paid": "Paye"}


class OpStudentFeeListWizard(models.TransientModel):
    _name = "op.student.fee.list.wizard"
    _description = "Liste des frais des eleves (impression / export)"

    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        default=lambda self: self.env.user.current_academic_year_id)
    classe_ids = fields.Many2many(
        "op.classe", string="Classes",
        domain="[('academic_year_id', '=', academic_year_id)]",
        help="Laisser vide pour inclure toutes les classes de l'annee academique.")
    fee_type_id = fields.Many2one("op.fee.type", string="Type de frais")
    academic_term_id = fields.Many2one("op.academic.term", string="Periode")
    state = fields.Selection(
        [("tous", "Tous"), ("draft", "Brouillon"), ("posted", "Comptabilise"),
         ("cancelled", "Annule")],
        string="Statut", default="tous", required=True)
    payment_state = fields.Selection(
        [("tous", "Tous"), ("not_paid", "Non paye"), ("partial", "Partiel"),
         ("paid", "Paye")],
        string="Statut paiement", default="tous", required=True)
    date_from = fields.Date(string="Du")
    date_to = fields.Date(string="Au")
    created_by_id = fields.Many2one("res.users", string="Cree par")

    file_data = fields.Binary(string="Fichier", readonly=True)
    file_name = fields.Char(string="Nom du fichier", readonly=True)

    preview_fee_ids = fields.Many2many(
        "op.student.fee", compute="_compute_preview", string="Apercu")
    preview_count = fields.Integer(compute="_compute_preview", string="Nombre de frais")

    @api.depends("academic_year_id", "classe_ids", "fee_type_id", "academic_term_id",
                 "state", "payment_state", "date_from", "date_to", "created_by_id")
    def _compute_preview(self):
        for wizard in self:
            fees = wizard._get_fees() if wizard.academic_year_id else self.env["op.student.fee"]
            wizard.preview_fee_ids = fees
            wizard.preview_count = len(fees)

    # ------------------------------------------------------------------
    # Selection des frais selon les filtres
    # ------------------------------------------------------------------
    def _get_fees(self):
        self.ensure_one()
        domain = []
        if self.classe_ids:
            domain.append(("classe_id", "in", self.classe_ids.ids))
        elif self.academic_year_id:
            domain.append(("academic_year_id", "=", self.academic_year_id.id))
        if self.fee_type_id:
            domain.append(("fee_type_id", "=", self.fee_type_id.id))
        if self.academic_term_id:
            domain.append(("academic_term_id", "=", self.academic_term_id.id))
        if self.state != "tous":
            domain.append(("state", "=", self.state))
        if self.payment_state != "tous":
            domain.append(("payment_state", "=", self.payment_state))
        if self.date_from:
            domain.append(("date", ">=", self.date_from))
        if self.date_to:
            domain.append(("date", "<=", self.date_to))
        if self.created_by_id:
            domain.append(("create_uid", "=", self.created_by_id.id))
        return self.env["op.student.fee"].search(domain, order="classe_id, student_id, date")

    # ------------------------------------------------------------------
    # Impression PDF
    # ------------------------------------------------------------------
    def action_print_pdf(self):
        self.ensure_one()
        if not self._get_fees():
            raise UserError(_("Aucun frais ne correspond a ces criteres."))
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_op_student_fee_list", self)

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
        fees = self._get_fees()
        if not fees:
            raise UserError(_("Aucun frais ne correspond a ces criteres."))

        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = book.add_worksheet(_("Frais"))

        f_title = book.add_format({"bold": True, "font_size": 14})
        f_head = book.add_format({
            "bold": True, "bg_color": "#714B67", "font_color": "#FFFFFF",
            "border": 1, "align": "center", "valign": "vcenter",
        })
        f_cell = book.add_format({"border": 1})
        f_date = book.add_format({"border": 1, "num_format": "dd/mm/yyyy"})
        f_amount = book.add_format({"border": 1, "num_format": "#,##0"})

        headers = [_("Date"), _("Eleve"), _("Classe"), _("Type de frais"),
                   _("Periode"), _("Montant"), _("Reste"), _("Statut")]
        sheet.write(0, 0, _("Liste des frais"), f_title)
        start = 2
        for c, label in enumerate(headers):
            sheet.set_column(c, c, 22)
            sheet.write(start, c, label, f_head)

        r = start + 1
        for fee in fees:
            sheet.write_datetime(r, 0, fee.date, f_date)
            sheet.write(r, 1, fee.student_id.name or "", f_cell)
            sheet.write(r, 2, fee.classe_id.display_name or "", f_cell)
            sheet.write(r, 3, fee.fee_type_id.name or "", f_cell)
            sheet.write(r, 4, fee.academic_term_id.display_name or "", f_cell)
            sheet.write(r, 5, fee.amount, f_amount)
            sheet.write(r, 6, fee.amount_residual, f_amount)
            sheet.write(r, 7, PAYMENT_STATE_LABELS.get(fee.payment_state, fee.payment_state or ""), f_cell)
            r += 1
        sheet.freeze_panes(start + 1, 0)
        book.close()
        output.seek(0)

        fname = "Liste_frais_%s.xlsx" % fields.Date.today().strftime("%Y%m%d")
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
