# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OpStudentRegistrationListWizard(models.TransientModel):
    _name = "op.student.registration.list.wizard"
    _description = "Liste des eleves inscrits sur une periode"

    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique", required=True,
        default=lambda self: self.env.user.current_academic_year_id)
    date_from = fields.Date(
        string="Inscrits entre le", required=True,
        default=lambda self: fields.Date.today().replace(month=1, day=1))
    date_to = fields.Date(
        string="et le", required=True, default=fields.Date.context_today)
    classe_ids = fields.Many2many(
        "op.classe", string="Classes",
        domain="[('academic_year_id', '=', academic_year_id)]",
        help="Laisser vide pour inclure toutes les classes de l'annee academique.")

    preview_count = fields.Integer(compute="_compute_preview", string="Nombre d'eleves")

    @api.depends("academic_year_id", "date_from", "date_to", "classe_ids")
    def _compute_preview(self):
        for wizard in self:
            wizard.preview_count = sum(
                len(lines) for _classe, lines in wizard._get_grouped_lines())

    # ------------------------------------------------------------------
    # Selection et regroupement
    # ------------------------------------------------------------------
    def _get_histories(self):
        self.ensure_one()
        if not self.academic_year_id:
            return self.env["op.student.enrollment.history"]
        domain = [
            ("academic_year_id", "=", self.academic_year_id.id),
            ("date_inscription", ">=", self.date_from),
            ("date_inscription", "<=", self.date_to),
        ]
        if self.classe_ids:
            domain.append(("classe_id", "in", self.classe_ids.ids))
        return self.env["op.student.enrollment.history"].search(domain)

    def _is_new_for_year(self, student):
        self.ensure_one()
        earlier = self.env["op.student.enrollment.history"].search([
            ("student_id", "=", student.id),
            ("academic_year_id", "!=", self.academic_year_id.id),
        ], limit=1)
        return not bool(earlier)

    def _get_grouped_lines(self):
        """Retourne [(classe, [historique, ...]), ...] tries par niveau puis
        nom de classe, chaque sous-liste triee par nom d'eleve."""
        self.ensure_one()
        histories = self._get_histories()
        by_classe = {}
        for history in histories:
            by_classe.setdefault(history.classe_id, self.env["op.student.enrollment.history"])
            by_classe[history.classe_id] |= history
        classes = sorted(by_classe, key=lambda c: (c.level_order, c.name))
        return [
            (classe, by_classe[classe].sorted(key=lambda h: h.student_id.name))
            for classe in classes
        ]

    def _get_gender_counts(self):
        self.ensure_one()
        histories = self._get_histories()
        students = histories.student_id
        return {
            "m": len(students.filtered(lambda s: s.gender == "m")),
            "f": len(students.filtered(lambda s: s.gender == "f")),
        }

    # ------------------------------------------------------------------
    # Impression
    # ------------------------------------------------------------------
    def action_print_pdf(self):
        self.ensure_one()
        if not self._get_histories():
            raise UserError(_("Aucun eleve inscrit sur cette periode."))
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_op_student_registration_list", self)
