# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OpStudentChangeClasseWizard(models.TransientModel):
    _name = "op.student.change.classe.wizard"
    _description = "Changer la classe d'un élève (transfert / redoublement)"

    student_id = fields.Many2one(
        "op.student", string="Élève", required=True, readonly=True)
    current_classe_id = fields.Many2one(
        "op.classe", string="Classe actuelle",
        related="student_id.classe_id", readonly=True)
    new_classe_id = fields.Many2one(
        "op.classe", string="Nouvelle classe", required=True,
        domain="[('academic_year_id', '=', current_academic_year_id)]")
    current_academic_year_id = fields.Many2one(
        "op.academic.year", related="student_id.classe_id.academic_year_id",
        readonly=True)

    motif = fields.Selection([
        ("transfer", "Transfert inter-classes"),
        ("redoublement", "Redoublement (même niveau)"),
        ("correction", "Correction de classe"),
    ], string="Motif", required=True, default="transfer")

    draft_fee_count = fields.Integer(
        string="Frais brouillons annulables",
        compute="_compute_fee_counts")
    posted_fee_count = fields.Integer(
        string="Frais comptabilisés (intacts)",
        compute="_compute_fee_counts")

    cancel_draft_fees = fields.Boolean(
        string="Annuler les frais brouillons de l'ancienne classe",
        default=True,
        help="Annule les frais encore en brouillon pour l'année en cours "
             "avant de régénérer les nouveaux. Les frais déjà comptabilisés "
             "(facture postée) ne sont jamais annulés automatiquement.")
    regenerate_fees = fields.Boolean(
        string="Régénérer les frais pour la nouvelle classe",
        default=True,
        help="Crée automatiquement les frais configurés sur la nouvelle classe "
             "pour l'élève (types de frais non encore présents uniquement).")

    @api.depends("student_id", "current_academic_year_id")
    def _compute_fee_counts(self):
        Fee = self.env["op.student.fee"]
        for rec in self:
            if not rec.student_id or not rec.current_academic_year_id:
                rec.draft_fee_count = 0
                rec.posted_fee_count = 0
                continue
            fees = Fee.search([
                ("student_id", "=", rec.student_id.id),
                ("academic_year_id", "=", rec.current_academic_year_id.id),
                ("state", "!=", "cancelled"),
            ])
            rec.draft_fee_count = len(fees.filtered(lambda f: f.state == "draft"))
            rec.posted_fee_count = len(fees.filtered(lambda f: f.state == "posted"))

    def action_confirm(self):
        self.ensure_one()
        student = self.student_id
        new_classe = self.new_classe_id
        year = self.current_academic_year_id

        if new_classe == student.classe_id:
            raise UserError(_(
                "La nouvelle classe est identique à la classe actuelle."))

        if year and self.cancel_draft_fees:
            draft_fees = self.env["op.student.fee"].search([
                ("student_id", "=", student.id),
                ("academic_year_id", "=", year.id),
                ("state", "=", "draft"),
            ])
            if draft_fees:
                draft_fees.action_cancel()

        vals = {"classe_id": new_classe.id}
        if self.motif == "redoublement":
            vals["redoublant"] = True

        student.with_context(skip_fee_generation=not self.regenerate_fees).write(vals)

        return {
            "type": "ir.actions.act_window",
            "res_model": "op.student",
            "view_mode": "form",
            "res_id": student.id,
            "target": "current",
        }
