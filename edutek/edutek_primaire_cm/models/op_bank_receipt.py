# -*- coding: utf-8 -*-
import base64
import io
import logging
import os
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class OpBankReceipt(models.Model):
    _name = "op.bank.receipt"
    _description = "Recu bancaire"
    _order = "date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Reference", required=True, default="/", copy=False, tracking=True)
    date = fields.Date(
        string="Date", required=True, default=fields.Date.context_today)
    amount = fields.Monetary(
        string="Montant recu", required=True, tracking=True)
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id)
    journal_id = fields.Many2one(
        "account.journal", string="Caisse / Banque",
        domain=[("type", "in", ("cash", "bank")), ("school_active", "=", True)])
    image = fields.Binary(string="Image du recu", attachment=True)
    image_filename = fields.Char()
    state = fields.Selection(
        [("draft", "Brouillon"), ("confirmed", "Confirme")],
        default="draft", readonly=True, tracking=True)
    ocr_raw = fields.Text(string="Texte OCR brut")

    fee_ids = fields.One2many("op.student.fee", "bank_receipt_id", string="Frais lies")

    amount_used = fields.Monetary(
        string="Montant utilise", compute="_compute_amounts", store=True,
        currency_field="currency_id")
    amount_remaining = fields.Monetary(
        string="Solde disponible", compute="_compute_amounts", store=True,
        currency_field="currency_id")

    @api.depends("amount", "fee_ids.move_id.amount_total",
                 "fee_ids.move_id.amount_residual", "fee_ids.state")
    def _compute_amounts(self):
        for rec in self:
            paid = sum(
                (fee.amount - (fee.amount_residual or 0.0))
                for fee in rec.fee_ids
                if fee.state == "posted"
            )
            rec.amount_used = paid
            rec.amount_remaining = rec.amount - paid

    def action_confirm(self):
        for rec in self:
            if rec.name == "/":
                seq = self.env["ir.sequence"].next_by_code("op.bank.receipt")
                rec.name = seq or "REC/%s" % fields.Date.today().strftime("%Y%m%d")
            rec.state = "confirmed"

    def action_reset_draft(self):
        for rec in self:
            if rec.fee_ids.filtered(lambda f: f.state == "posted"):
                raise UserError(
                    _("Impossible de repasser en brouillon : des frais sont deja "
                      "comptabilises avec ce recu."))
            rec.state = "draft"

    def action_run_ocr(self):
        self.ensure_one()
        if not self.image:
            raise UserError(_("Veuillez uploader une image du recu avant de lancer l'OCR."))
        try:
            import pytesseract
        except ImportError:
            raise UserError(_(
                "Tesseract n'est pas installe.\n"
                "Executez : sudo apt install tesseract-ocr tesseract-ocr-fra "
                "&& pip install pytesseract"))

        from PIL import Image, ImageEnhance, ImageFilter

        raw_bytes = base64.b64decode(self.image)
        img = Image.open(io.BytesIO(raw_bytes)).convert("L")

        # Scale up small images — Tesseract accuracy drops below ~150 DPI.
        w, h = img.size
        if w < 1500:
            scale = max(2, 1500 // w)
            img = img.resize((w * scale, h * scale), Image.LANCZOS)

        img = ImageEnhance.Contrast(img).enhance(1.8)
        img = img.filter(ImageFilter.SHARPEN)

        config = "--oem 3 --psm 3"
        text = pytesseract.image_to_string(img, lang="fra+eng", config=config)
        self.ocr_raw = text

        def _clean_amount(raw_str):
            s = re.sub(r"\s+", "", raw_str.strip())
            # French/Cameroonian format: "344.500" = 344 500 (period = thousands sep)
            # Detect: digits, then one or more groups of .NNN
            if re.match(r"^\d{1,3}(\.\d{3})+$", s):
                s = s.replace(".", "")
            else:
                # comma as thousands sep: "345,000" -> strip comma
                s = re.sub(r",(\d{3})(?!\d)", r"\1", s)
                s = s.replace(",", ".")
            s = s.rstrip(".")
            try:
                val = float(s)
                return val if val > 0 else None
            except ValueError:
                return None

        # Amount extraction — priority order for Cameroonian bank receipts
        amount_val = None
        for pat in [
            # BGFIBank: "XAF : 669.000 Valeur" = montant NET crédité (priorité max)
            r"\bXAF\s*[:;+]\s*([\d.,]+)\s+Valeur",
            # BGFIBank: "Total recu : 670 000" ou "Total recu 670 000"
            r"total\s+re[cç]u\s*[:;=+]?\s*([\d\s.,]+)",
            # BGFIBank/EduTek: "Montant versé : 670 000" — [:;] car OCR confond : et ;
            r"montant\s+vers[eé]\s*[:;=+]\s*([\d\s.,]+)",
            # EduTek: "MONTANT VERSE 50 000 F" sans ponctuation
            r"montant\s+vers[eé][^\d]*([\d\s.,]+)",
            # EduTek: "Recu au montant de"
            r"re[cç]u\s+au\s+montant\s+de[^\d]*([\d\s.,]+)",
            # Facture commerciale: "TOTAL TTC... 360000"
            r"total\s+ttc[^\d]*([\d\s.,]+)",
            # Generic
            r"(?:montant|amount|FCFA|CFA)[^\d]*([\d\s.,]{4,})",
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                v = _clean_amount(m.group(1))
                if v:
                    amount_val = v
                    break

        # Fallback — largest grouped number >= 1000
        if not amount_val:
            candidates = re.findall(r"\d{1,3}(?:[\s.]\d{3})+", text)
            valid = [v for v in (_clean_amount(c) for c in candidates) if v and v >= 1000]
            if valid:
                amount_val = max(valid)

        # Reference extraction
        ref_val = None
        for pat in [
            # BGFIBank: "OPERATION N° 415806" — N° souvent garbled en Ne/N'/No/N
            r"op[eé]ration\s+n[e°o®º+²'\s]{0,4}(\d{4,})",
            # Facture commerciale: "FACTURE N° C0001376" ou "FACTURE No 30001376"
            r"facture\s+n[°o'\s.]{0,3}([A-Z0-9]{4,})",
            # EduTek: "FRAIS-2026-2440"
            r"([A-Z]{2,10}-\d{4}-\d+)",
            # BGFIBank ligne de crédit: "N' 40022972011-78 XAF" ou "N° 40022972011-78 XAF"
            # Apparaît quand le n° d'opération est illisible mais l'IBAN est présent
            r"N['’°\s]\s*(\d{7,}[-]\d{2,})\s+XAF",
            # Generic label + ref
            r"(?:ref(?:erence)?|n[°o®]{0,2}|num[eé]ro|transaction|txn)[^\w]*([A-Z0-9]{4,}[-/][A-Z0-9]+)",
            r"(?:ref(?:erence)?|n[°o®]{0,2}|transaction|txn)[^\w]*([A-Z0-9]{5,})",
            # Compte multilignes: "Compte\n: 40022972011" (layout 2 colonnes BGFIBank)
            r"compte[\s\S]{0,30}?(\d{8,})",
            # Compte inline
            r"(?:compte|account)\s*[:;=]?\s*(\d{8,})",
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                ref_val = m.group(1).strip()
                break

        if ref_val:
            self.name = ref_val
        if amount_val:
            self.amount = amount_val

        if not ref_val and not amount_val:
            raise UserError(_(
                "L'OCR n'a pas pu extraire de donnees exploitables.\n"
                "Essayez avec une image plus nette ou saisissez la reference "
                "et le montant manuellement."))

    @api.model
    def _cron_import_from_canon_scanner(self):
        scan_dir = self.env["ir.config_parameter"].sudo().get_param(
            "edutek.canon_scan_dir", "/mnt/canon_scans/")
        if not os.path.isdir(scan_dir):
            _logger.warning("EduTek: scanner folder not found: %s", scan_dir)
            return

        journal = self.env["account.journal"].search([
            ("type", "in", ("cash", "bank")),
            ("school_active", "=", True),
        ], limit=1)

        for filename in sorted(os.listdir(scan_dir)):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            file_path = os.path.join(scan_dir, filename)
            try:
                with open(file_path, "rb") as f:
                    image_data = f.read()

                receipt = self.create({
                    "image": base64.b64encode(image_data),
                    "image_filename": filename,
                    "journal_id": journal.id if journal else False,
                    "amount": 0,
                    "state": "draft",
                })
                os.remove(file_path)

                try:
                    receipt.action_run_ocr()
                except Exception as ocr_err:
                    _logger.warning(
                        "EduTek OCR: failed to parse %s -- %s", filename, ocr_err)

                _logger.info("EduTek: imported scanned receipt %s -> id=%d", filename, receipt.id)
            except Exception as e:
                _logger.error("EduTek: error processing scanner file %s -- %s", filename, e)
