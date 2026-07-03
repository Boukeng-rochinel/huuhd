# -*- coding: utf-8 -*-
import base64
import io

from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

CYCLE_SECTION_LABELS = {
    ("maternelle", False): "Maternelle",
    ("primaire", False): "Primaire",
    ("secondaire", False): "Secondaire",
    ("maternelle", True): "Nursery",
    ("primaire", True): "Primary",
    ("secondaire", True): "Secondary",
}


class OpCashCollectionWizard(models.TransientModel):
    _name = "op.cash.collection.wizard"
    _description = "Etat des encaissements sur frais exigibles"

    date_from = fields.Date(
        string="Allant du", required=True,
        default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(
        string="Au", required=True, default=fields.Date.context_today)
    classe_ids = fields.Many2many(
        "op.classe", string="Salles (classes)",
        help="Laisser vide pour inclure toutes les salles.")
    journal_ids = fields.Many2many(
        "account.journal", string="Caisses",
        domain=[("type", "in", ("cash", "bank")), ("school_active", "=", True)],
        help="Laisser vide pour inclure toutes les caisses/comptes.")
    created_by_id = fields.Many2one("res.users", string="Encaisse par")

    preview_count = fields.Integer(compute="_compute_preview", string="Nombre de recus")

    file_data = fields.Binary(string="Fichier", readonly=True)
    file_name = fields.Char(string="Nom du fichier", readonly=True)

    @api.depends("date_from", "date_to", "classe_ids", "journal_ids", "created_by_id")
    def _compute_preview(self):
        for wizard in self:
            wizard.preview_count = len(wizard._get_rows())

    # ------------------------------------------------------------------
    # Selection des paiements (un encaissement = un account.payment relie,
    # par reconciliation, a la facture d'un op.student.fee)
    # ------------------------------------------------------------------
    def _get_rows(self):
        self.ensure_one()
        fees = self.env["op.student.fee"].search([
            ("move_id", "!=", False), ("state", "=", "posted")])
        move_to_fee = {fee.move_id.id: fee for fee in fees}
        if not move_to_fee:
            return []
        domain = [
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
            ("state", "not in", ("draft", "cancel")),
            ("reconciled_invoice_ids", "in", list(move_to_fee.keys())),
        ]
        if self.journal_ids:
            domain.append(("journal_id", "in", self.journal_ids.ids))
        if self.created_by_id:
            domain.append(("create_uid", "=", self.created_by_id.id))
        payments = self.env["account.payment"].search(domain, order="date, id")

        rows = []
        for payment in payments:
            fee = None
            for invoice in payment.reconciled_invoice_ids:
                if invoice.id in move_to_fee:
                    fee = move_to_fee[invoice.id]
                    break
            if not fee:
                continue
            if self.classe_ids and fee.classe_id not in self.classe_ids:
                continue
            rows.append({"payment": payment, "fee": fee})
        return rows

    @api.model
    def _fee_category(self, fee_type):
        if fee_type.is_registration_fee:
            return _("Frais d'inscription")
        if fee_type.is_miscellaneous:
            return _("Frais divers")
        return _("Frais de scolarite")

    @api.model
    def _cycle_section_label(self, classe):
        if not classe:
            return _("Autre")
        return CYCLE_SECTION_LABELS.get((classe.cycle, classe.is_anglophone), _("Autre"))

    def _get_summary(self, rows):
        self.ensure_one()
        by_day, by_category, by_journal, by_cycle = {}, {}, {}, {}
        for row in rows:
            payment, fee = row["payment"], row["fee"]
            by_day[payment.date] = by_day.get(payment.date, 0.0) + payment.amount
            cat = self._fee_category(fee.fee_type_id)
            by_category[cat] = by_category.get(cat, 0.0) + payment.amount
            jname = payment.journal_id.name
            by_journal[jname] = by_journal.get(jname, 0.0) + payment.amount
            cyc = self._cycle_section_label(fee.classe_id)
            by_cycle[cyc] = by_cycle.get(cyc, 0.0) + payment.amount
        registration_count = len(
            [r for r in rows if r["fee"].fee_type_id.is_registration_fee])
        return {
            "total_amount": sum(r["payment"].amount for r in rows),
            "total_count": len(rows),
            "nb_jours": len(by_day),
            "by_day": sorted(by_day.items()),
            "by_category": by_category,
            "by_journal": by_journal,
            "by_cycle": by_cycle,
            "registration_count": registration_count,
        }

    # ------------------------------------------------------------------
    # Impression
    # ------------------------------------------------------------------
    def action_print_daily(self):
        self.ensure_one()
        if not self._get_rows():
            raise UserError(_("Aucun encaissement sur cette periode."))
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_op_cash_collection_daily", self)

    def action_print_ledger(self):
        self.ensure_one()
        if not self._get_rows():
            raise UserError(_("Aucun encaissement sur cette periode."))
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_op_cash_collection_ledger", self)

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
        rows = self._get_rows()
        if not rows:
            raise UserError(_("Aucun encaissement sur cette periode."))

        output = io.BytesIO()
        book = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = book.add_worksheet(_("Encaissements"))

        f_title = book.add_format({"bold": True, "font_size": 14})
        f_head = book.add_format({
            "bold": True, "bg_color": "#714B67", "font_color": "#FFFFFF",
            "border": 1, "align": "center", "valign": "vcenter",
        })
        f_cell = book.add_format({"border": 1})
        f_date = book.add_format({"border": 1, "num_format": "dd/mm/yyyy"})
        f_amount = book.add_format({"border": 1, "num_format": "#,##0"})

        headers = [_("Date"), _("N° recu"), _("Salle"), _("Eleve"),
                   _("Type de frais"), _("Montant"), _("Caisse")]
        sheet.write(0, 0, _("Etat des encaissements"), f_title)
        start = 2
        for c, label in enumerate(headers):
            sheet.set_column(c, c, 22)
            sheet.write(start, c, label, f_head)

        r = start + 1
        for row in rows:
            payment, fee = row["payment"], row["fee"]
            sheet.write_datetime(r, 0, payment.date, f_date)
            sheet.write(r, 1, payment.name or "", f_cell)
            sheet.write(r, 2, fee.classe_id.display_name or "", f_cell)
            sheet.write(r, 3, fee.student_id.name or "", f_cell)
            sheet.write(r, 4, fee.fee_type_id.name or "", f_cell)
            sheet.write(r, 5, payment.amount, f_amount)
            sheet.write(r, 6, payment.journal_id.name or "", f_cell)
            r += 1
        sheet.freeze_panes(start + 1, 0)
        book.close()
        output.seek(0)

        fname = "Encaissements_%s.xlsx" % fields.Date.today().strftime("%Y%m%d")
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
