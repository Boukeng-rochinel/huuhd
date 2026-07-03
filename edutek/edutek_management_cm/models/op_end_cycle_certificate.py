# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class OpEndCycleCertificate(models.Model):
    _name = "op.end.cycle.certificate"
    _description = "Certificat / attestation de promotion"
    _order = "date_delivrance desc, id desc"

    name = fields.Char(string="Reference", default="/", readonly=True, copy=False)
    student_id = fields.Many2one("op.student", string="Eleve", required=True, ondelete="cascade")
    classe_origine_id = fields.Many2one(
        "op.classe", string="Classe d'origine", required=True)
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        related="classe_origine_id.academic_year_id", store=True, readonly=True)

    classe_destination_id = fields.Many2one(
        "op.classe", string="Classe de destination (si connue)",
        help="A renseigner si la classe de l'eleve pour l'annee suivante est "
             "deja decidee. Sinon, n'indiquer que le cycle de destination.")
    cycle_destination = fields.Selection(
        [("maternelle", "Maternelle"), ("primaire", "Primaire"), ("secondaire", "Secondaire")],
        string="Cycle de destination")

    is_cycle_end = fields.Boolean(
        string="Fin de cycle", compute="_compute_is_cycle_end", store=True,
        help="Coche automatiquement quand la classe d'origine et le cycle de "
             "destination appartiennent a des cycles differents (ex: Maternelle "
             "-> Primaire). Change le libelle imprime sur le document.")

    mention = fields.Selection(
        [
            ("passable", "Passable"),
            ("assez_bien", "Assez Bien"),
            ("bien", "Bien"),
            ("tres_bien", "Tres Bien"),
            ("excellent", "Excellent"),
        ],
        string="Mention")
    date_delivrance = fields.Date(string="Date de delivrance", default=fields.Date.context_today)
    note = fields.Text(string="Note")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)

    @api.onchange("classe_destination_id")
    def _onchange_classe_destination_id(self):
        if self.classe_destination_id:
            self.cycle_destination = self.classe_destination_id.cycle

    @api.depends("classe_origine_id.cycle", "cycle_destination")
    def _compute_is_cycle_end(self):
        for rec in self:
            rec.is_cycle_end = bool(
                rec.classe_origine_id.cycle and rec.cycle_destination
                and rec.classe_origine_id.cycle != rec.cycle_destination
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "/") == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "op.end.cycle.certificate") or "/"
        return super().create(vals_list)

    def action_print(self):
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_management_cm.action_report_op_end_cycle_certificate", self)

    def action_print_2up(self):
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_management_cm.action_report_op_end_cycle_certificate_2up", self)
