# -*- coding: utf-8 -*-
from odoo import _, fields, models


class OpClosureDiagnosticWizard(models.TransientModel):
    _name = "op.closure.diagnostic.wizard"
    _description = "Diagnostic des annees academiques et de l'acces aux classes"

    classe_id_to_check = fields.Integer(
        string="ID de classe a verifier (optionnel)",
        help="Le numero entre parentheses dans un message d'erreur du type "
             "'Erreur d'acces ... (op.classe: 32)'.")
    report = fields.Text(string="Rapport", readonly=True)

    def action_diagnose(self):
        self.ensure_one()
        lines = []

        # ------------------------------------------------------------------
        # 1. Toutes les annees academiques - pour reperer les doublons de nom
        # ------------------------------------------------------------------
        years = self.env["op.academic.year"].sudo().search([], order="start_date")
        lines.append(_("=== Annees academiques (%d) ===") % len(years))
        names_seen = {}
        for year in years:
            names_seen.setdefault(year.name, []).append(year.id)
            lines.append(_("ID %(id)s : %(name)s (%(start)s -> %(end)s) - %(closed)s") % {
                "id": year.id, "name": year.name,
                "start": year.start_date, "end": year.end_date,
                "closed": _("cloturee") if year.is_closed else _("ouverte"),
            })
        duplicates = {name: ids for name, ids in names_seen.items() if len(ids) > 1}
        lines.append("")
        if duplicates:
            lines.append(_("/!\\ NOMS EN DOUBLE DETECTES (cause probable des erreurs d'acces) :"))
            for name, ids in duplicates.items():
                lines.append(_("  '%(name)s' existe %(count)d fois (ids : %(ids)s)") % {
                    "name": name, "count": len(ids), "ids": ids,
                })
        else:
            lines.append(_("Aucun nom d'annee en double."))

        # ------------------------------------------------------------------
        # 2. Annee courante de l'utilisateur (selecteur en haut a droite)
        # ------------------------------------------------------------------
        lines.append("")
        lines.append(_("=== Votre annee courante ==="))
        current = self.env.user.current_academic_year_id
        if current:
            lines.append(_("ID %(id)s : %(name)s") % {"id": current.id, "name": current.name})
        else:
            lines.append(_("Aucune annee courante definie pour votre utilisateur."))

        # ------------------------------------------------------------------
        # 3. Verification d'une classe precise (reproduit exactement le
        #    controle d'acces que l'application fait, pour voir s'il echoue)
        # ------------------------------------------------------------------
        if self.classe_id_to_check:
            lines.append("")
            lines.append(_("=== Verification de la classe ID %d ===") % self.classe_id_to_check)
            classe_sudo = self.env["op.classe"].sudo().browse(self.classe_id_to_check)
            if not classe_sudo.exists():
                lines.append(_("Cette classe n'existe pas (ou plus) en base."))
            else:
                lines.append(_("Nom : %s") % (classe_sudo.name or "(sans nom)"))
                lines.append(_("Annee academique de cette classe : ID %(id)s : %(name)s") % {
                    "id": classe_sudo.academic_year_id.id,
                    "name": classe_sudo.academic_year_id.name,
                })
                if current:
                    if classe_sudo.academic_year_id.id == current.id:
                        lines.append(_("=> Correspond a votre annee courante (meme ID)."))
                    else:
                        lines.append(_(
                            "=> NE CORRESPOND PAS a votre annee courante (ID different, "
                            "meme si le nom affiche peut etre identique) : c'est exactement "
                            "ce qui declenche l'erreur d'acces."))

                found_normal = self.env["op.classe"].search(
                    [("id", "=", self.classe_id_to_check)])
                found_all_years = self.env["op.classe"].with_context(
                    academic_year_all=True).search([("id", "=", self.classe_id_to_check)])
                lines.append(_("Visible en recherche normale (comme dans l'application) : %s") % (
                    _("Oui") if found_normal else _("Non")))
                lines.append(_("Visible en ignorant le filtre par annee academique : %s") % (
                    _("Oui") if found_all_years else _("Non")))
                if found_all_years and not found_normal:
                    lines.append(_(
                        "=> Confirme : le filtre automatique par annee academique "
                        "courante est la cause de l'erreur d'acces sur cette classe."))

        self.report = "\n".join(str(line) for line in lines)
        return True
