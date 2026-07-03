# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class OpClasseFeeBilanWizard(models.TransientModel):
    _name = "op.classe.fee.bilan.wizard"
    _description = "Bilan des frais par classe"

    academic_year_id = fields.Many2one(
        "op.academic.year", string="Année académique", required=True,
        default=lambda self: self.env.user.current_academic_year_id)
    classe_ids = fields.Many2many(
        "op.classe", string="Classes",
        domain="[('academic_year_id', '=', academic_year_id)]",
        help="Laissez vide pour inclure toutes les classes de l'année.")
    fee_type_ids = fields.Many2many(
        "op.fee.type", string="Types de frais",
        help="Laissez vide pour tous les types de frais.")
    show_detail_by_type = fields.Boolean(
        string="Détail par type de frais", default=True)
    show_insolvable_only = fields.Boolean(
        string="Insolvables uniquement", default=False,
        help="N'affiche que les classes ayant un reste à payer.")

    def _get_bilan_data(self):
        """Calcule les statistiques de frais par classe."""
        self.ensure_one()
        Fee = self.env["op.student.fee"]
        Classe = self.env["op.classe"]

        domain_classe = [("academic_year_id", "=", self.academic_year_id.id)]
        if self.classe_ids:
            domain_classe.append(("id", "in", self.classe_ids.ids))
        classes = Classe.search(domain_classe, order="name")

        domain_fee = [
            ("academic_year_id", "=", self.academic_year_id.id),
            ("state", "=", "posted"),
        ]
        if self.fee_type_ids:
            domain_fee.append(("fee_type_id", "in", self.fee_type_ids.ids))

        result = []
        for classe in classes:
            fees = Fee.search(domain_fee + [("classe_id", "=", classe.id)])
            if not fees:
                continue

            total_du = sum(fees.mapped("amount"))
            total_paye = sum(f.amount - f.amount_residual for f in fees)
            total_reste = sum(fees.mapped("amount_residual"))
            taux = round(total_paye / total_du * 100, 1) if total_du else 0.0

            if self.show_insolvable_only and total_reste == 0:
                continue

            detail_by_type = {}
            if self.show_detail_by_type:
                for fee in fees:
                    ft = fee.fee_type_id
                    if ft not in detail_by_type:
                        detail_by_type[ft] = {
                            "name": ft.name,
                            "du": 0.0,
                            "paye": 0.0,
                            "reste": 0.0,
                            "count": 0,
                        }
                    detail_by_type[ft]["du"] += fee.amount
                    detail_by_type[ft]["paye"] += fee.amount - fee.amount_residual
                    detail_by_type[ft]["reste"] += fee.amount_residual
                    detail_by_type[ft]["count"] += 1

            result.append({
                "classe": classe,
                "effectif": len(fees.mapped("student_id")),
                "nb_soldes": len(fees.filtered(
                    lambda f: f.payment_state == "paid").mapped("student_id")),
                "total_du": total_du,
                "total_paye": total_paye,
                "total_reste": total_reste,
                "taux": taux,
                "detail": list(detail_by_type.values()),
            })
        return result

    def action_print_pdf(self):
        self.ensure_one()
        return self.env["ir.actions.report"].build_print_preview_action(
            "edutek_primaire_cm.action_report_classe_fee_bilan", self)

    def action_view_html(self):
        self.ensure_one()
        return self.env["ir.actions.report"]._render_qweb_html(
            "edutek_primaire_cm.action_report_classe_fee_bilan", self.ids)[0]
