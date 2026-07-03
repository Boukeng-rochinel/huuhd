# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.fields import Domain


class AcademicYearFilterMixin(models.AbstractModel):
    """A inclure dans les modeles possedant un champ academic_year_id.
    Filtre automatiquement toutes les recherches OUVERTES (listes, kanban,
    dropdowns Many2one...) sur l'annee academique en cours de l'utilisateur,
    sauf si :
      - le domaine filtre deja explicitement sur academic_year_id
      - le domaine filtre deja explicitement sur un champ de _SKIP_FIELDS
        (cf. note ci-dessous : une recherche "precise", pas une liste ouverte)
      - le contexte contient la cle 'academic_year_all' (echappatoire pour les
        ecrans qui doivent volontairement montrer toutes les annees).

    Le filtre sur id/classe_id est essentiel : Odoo resout les relations
    (Many2one affiche dans un formulaire/kanban, One2many du type
    classe.student_ids, calcul de champs lies...) via des appels internes du
    type _search([('id', 'in', [32])]) ou _search([('classe_id', '=', 5)]) -
    sans cette echappatoire, ce mixin bloquait/videait silencieusement TOUT
    acces a un enregistrement (classe, eleve...) ou a un decompte
    (student_count...) dont l'annee differe de l'annee courante de
    l'utilisateur, meme en consultant un enregistrement precis plutot
    qu'une liste ouverte (Odoo rapportait alors une erreur d'acces 'Access
    Denied by record rules', comme si une vraie regle d'enregistrement
    (ir.rule) etait en cause - ou, pour un compteur, affichait silencieusement
    0 au lieu du vrai total)."""
    _name = "op.academic.year.filter.mixin"
    _description = "Filtre par annee academique en cours"

    _SKIP_FIELDS = ("academic_year_id", "id", "classe_id")

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        domain = Domain(domain)
        if not self.env.context.get("academic_year_all") and not any(
            cond.field_expr in self._SKIP_FIELDS for cond in domain.iter_conditions()
        ):
            year = self.env.user.current_academic_year_id
            if year:
                domain &= Domain("academic_year_id", "=", year.id)
        return super()._search(domain, offset=offset, limit=limit, order=order, **kwargs)
