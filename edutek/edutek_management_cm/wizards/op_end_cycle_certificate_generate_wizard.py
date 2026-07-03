# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OpEndCycleCertificateGenerateWizard(models.TransientModel):
    _name = "op.end.cycle.certificate.generate.wizard"
    _description = "Generation en masse des certificats de promotion"

    classe_origine_id = fields.Many2one(
        "op.classe", string="Classe d'origine", required=True)
    classe_destination_id = fields.Many2one(
        "op.classe", string="Classe de destination (si connue)",
        help="A renseigner si la classe de l'eleve pour l'annee suivante est "
             "deja decidee. Sinon, n'indiquer que le cycle de destination.")
    cycle_destination = fields.Selection(
        [("maternelle", "Maternelle"), ("primaire", "Primaire"), ("secondaire", "Secondaire")],
        string="Cycle de destination")
    student_ids = fields.Many2many(
        "op.student", string="Eleves",
        domain="[('classe_id', '=', classe_origine_id)]")
    skip_existing = fields.Boolean(
        string="Reutiliser les certificats existants", default=True,
        help="Si un certificat existe deja pour un eleve et cette classe "
             "d'origine, ses informations de destination sont mises a jour "
             "plutot que d'en creer un second.")

    @api.onchange("classe_origine_id")
    def _onchange_classe_origine_id(self):
        if self.classe_origine_id:
            self.student_ids = self.env["op.student"].search(
                [("classe_id", "=", self.classe_origine_id.id)])
        else:
            self.student_ids = False

    @api.onchange("classe_destination_id")
    def _onchange_classe_destination_id(self):
        if self.classe_destination_id:
            self.cycle_destination = self.classe_destination_id.cycle

    def _generate(self):
        self.ensure_one()
        if not self.student_ids:
            raise UserError(_("Aucun eleve selectionne."))
        Certificate = self.env["op.end.cycle.certificate"]
        certificates = Certificate
        for student in self.student_ids:
            existing = Certificate
            if self.skip_existing:
                existing = Certificate.search([
                    ("student_id", "=", student.id),
                    ("classe_origine_id", "=", self.classe_origine_id.id),
                ], limit=1)
            if existing:
                existing.write({
                    "classe_destination_id": self.classe_destination_id.id,
                    "cycle_destination": self.cycle_destination,
                })
                certificates |= existing
            else:
                certificates |= Certificate.create({
                    "student_id": student.id,
                    "classe_origine_id": self.classe_origine_id.id,
                    "classe_destination_id": self.classe_destination_id.id,
                    "cycle_destination": self.cycle_destination,
                })
        return certificates

    def action_generate_and_print(self):
        certificates = self._generate()
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_management_cm.action_report_op_end_cycle_certificate", certificates)

    def action_generate_and_print_2up(self):
        certificates = self._generate()
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_management_cm.action_report_op_end_cycle_certificate_2up", certificates)
