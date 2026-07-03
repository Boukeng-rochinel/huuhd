# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    op_classroom_count = fields.Integer(string="Nombre de salles de classe")

    @api.model
    def get_sis_dashboard_data(self):
        """Agrege en un seul appel les chiffres affiches sur le tableau de
        bord EduTek (ecran d'accueil), pour eviter les allers-retours
        multiples depuis le composant OWL."""
        company = self.env.company

        # Le mixin op.academic.year.filter.mixin (sur op.student et
        # op.classe) filtre silencieusement toute recherche sur l'annee
        # academique en cours de l'utilisateur. On le neutralise ici via le
        # contexte pour garder le controle explicite du domaine.
        Student = self.env["op.student"].with_context(academic_year_all=True)
        Classe = self.env["op.classe"].with_context(academic_year_all=True)
        # sudo() : "Frais des eleves" est reserve aux Managers (groupe
        # EduTek/Manager), mais le tableau de bord (vu par tous les
        # utilisateurs EduTek) n'affiche ici qu'un libelle + une date des
        # dernieres recettes, sans donnee sensible (montant, eleve...) -
        # une elevation ponctuelle est plus sure que d'ouvrir l'acces au
        # modele complet juste pour ce widget.
        Fee = self.env["op.student.fee"].sudo()

        year = self.env.user.current_academic_year_id
        if not year:
            year = self.env["op.academic.year"].search(
                [], order="start_date desc", limit=1)

        classes_count = Classe.search_count(
            [("academic_year_id", "=", year.id)] if year else [])

        active_students = Student.search([("active", "=", True)])
        inscrits = active_students.filtered(lambda s: s.inscription_state == "inscrit")
        non_inscrits = active_students - inscrits
        demission_count = Student.search_count([("active", "=", False)])

        nouveaux = inscrits.filtered(lambda s: s.enrollment_type == "nouveau")
        anciens = inscrits.filtered(lambda s: s.enrollment_type == "ancien")

        boys = len(inscrits.filtered(lambda s: s.gender == "m"))
        girls = len(inscrits.filtered(lambda s: s.gender == "f"))
        staff_child_count = len(active_students.filtered("enfant_enseignant"))

        recent_fees = Fee.search([("state", "=", "posted")], order="date desc", limit=5)
        recent_ops = [{
            "date": fee.date.strftime("%d/%m/%Y") if fee.date else "",
            "label": "Recette - %s" % (fee.fee_type_id.name or "").upper(),
        } for fee in recent_fees]

        recent_birthdays = self._get_upcoming_birthdays(active_students)

        return {
            "company_name": company.name,
            "country_name": company.country_id.name or "",
            "academic_year_name": year.name if year else "",
            "classes_count": classes_count,
            "classroom_count": company.op_classroom_count,
            "inscrits": len(inscrits),
            "non_inscrits": len(non_inscrits),
            "demission": demission_count,
            "staff_child_count": staff_child_count,
            "total_students": len(inscrits) + len(non_inscrits),
            "nouveaux": len(nouveaux),
            "anciens": len(anciens),
            "boys": boys,
            "girls": girls,
            "recent_ops": recent_ops,
            "birthdays": recent_birthdays,
        }

    def _get_upcoming_birthdays(self, students, within_days=14, limit=5):
        today = fields.Date.context_today(self)
        upcoming = []
        for student in students.filtered("birth_date"):
            next_bday = self._next_occurrence(student.birth_date, today)
            days = (next_bday - today).days
            if days <= within_days:
                upcoming.append({"name": student.name, "days": days})
        upcoming.sort(key=lambda b: b["days"])
        return upcoming[:limit]

    def _next_occurrence(self, birth_date, today):
        """Prochaine date anniversaire >= aujourd'hui (gere le 29 fevrier)."""
        for year_offset in (0, 1):
            try:
                candidate = birth_date.replace(year=today.year + year_offset)
            except ValueError:
                candidate = birth_date.replace(year=today.year + year_offset, day=28)
            if candidate >= today:
                return candidate
        return candidate
