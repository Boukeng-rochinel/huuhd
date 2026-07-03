# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class OpBulletinGenerateWizard(models.TransientModel):
    _name = "op.bulletin.generate.wizard"
    _description = "Generer les bulletins en masse"

    academic_term_id = fields.Many2one(
        "op.academic.term", string="Periode", required=True,
        help="Choisir une Sequence pour generer les bulletins habituels a "
             "partir des notes saisies. Choisir un Trimestre pour generer "
             "le bulletin trimestriel agrege a partir des bulletins de ses "
             "2 sequences (necessite qu'elles existent deja pour l'eleve).")
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        related="academic_term_id.academic_year_id", readonly=True)
    classe_ids = fields.Many2many(
        "op.classe", string="Classes",
        domain="[('academic_year_id', '=', academic_year_id)]",
        help="Laisser vide pour generer les bulletins de toutes les classes "
             "de l'annee academique.")

    @staticmethod
    def _get_appreciation(moyenne):
        if moyenne >= 16:
            return "Excellent"
        elif moyenne >= 14:
            return "Tres Bien"
        elif moyenne >= 12:
            return "Bien"
        elif moyenne >= 10:
            return "Assez Bien"
        elif moyenne >= 8:
            return "Passable"
        return "Insuffisant"

    def _get_line_vals_from_marks(self, student):
        """Mode Sequence (periode-feuille) : une ligne par note saisie."""
        Mark = self.env["op.student.mark"]
        marks = Mark.search([
            ("student_id", "=", student.id),
            ("academic_term_id", "=", self.academic_term_id.id),
        ])
        return [
            (0, 0, {
                "subject_id": mark.subject_id.id,
                "coefficient": mark.coefficient,
                "note": mark.note,
                "sequence": mark.classe_subject_id.sequence,
            })
            for mark in marks.sorted(key=lambda m: m.classe_subject_id.sequence)
        ]

    def _get_line_vals_from_children(self, student, expected_children):
        """Mode Trimestre (periode-conteneur) : pas de notes directes, on
        agrege les bulletins deja generes de ses sequences. Par matiere, la
        note trimestrielle est la moyenne des notes disponibles parmi les
        sequences attendues (1 seule sequence attendue, ex. classe d'examen
        arretee a la Sequence 5 -> la note de cette sequence est reprise
        telle quelle, pas de moyenne a faire). Renvoie None si le bulletin
        d'au moins une sequence attendue manque encore pour cet eleve
        (mieux vaut ne pas generer un trimestre incomplet que d'en generer
        un silencieusement faux)."""
        Bulletin = self.env["op.bulletin"]
        child_bulletins = Bulletin.search([
            ("student_id", "=", student.id),
            ("academic_term_id", "in", expected_children.ids),
        ])
        if len(child_bulletins) < len(expected_children):
            return None

        by_subject = {}
        for line in child_bulletins.line_ids:
            by_subject.setdefault(line.subject_id, []).append(line)
        line_vals = []
        for subject, lines in by_subject.items():
            avg_note = sum(line.note for line in lines) / len(lines)
            line_vals.append((0, 0, {
                "subject_id": subject.id,
                "coefficient": lines[0].coefficient,
                "note": avg_note,
                "sequence": lines[0].sequence,
            }))
        return line_vals

    def action_generate(self):
        self.ensure_one()
        classes = self.classe_ids or self.env["op.classe"].search(
            [("academic_year_id", "=", self.academic_term_id.academic_year_id.id)])
        if not classes:
            raise UserError(_("Aucune classe trouvee pour cette annee academique."))

        is_trimestre = bool(self.academic_term_id.child_term_ids)

        Bulletin = self.env["op.bulletin"]
        all_bulletins = Bulletin
        skipped_classes = 0
        skipped_students = 0

        for classe in classes:
            applicable = classe._get_applicable_terms()

            if is_trimestre:
                expected_children = self.academic_term_id.child_term_ids & applicable
                if not expected_children:
                    skipped_classes += 1
                    continue
            else:
                if self.academic_term_id not in applicable:
                    skipped_classes += 1
                    continue

            bulletins = Bulletin
            for student in classe.student_ids:
                if is_trimestre:
                    line_vals = self._get_line_vals_from_children(student, expected_children)
                    if line_vals is None:
                        skipped_students += 1
                        continue
                else:
                    line_vals = self._get_line_vals_from_marks(student)

                bulletin = Bulletin.search([
                    ("student_id", "=", student.id),
                    ("academic_term_id", "=", self.academic_term_id.id),
                ], limit=1)
                if not bulletin:
                    bulletin = Bulletin.create({
                        "student_id": student.id,
                        "academic_term_id": self.academic_term_id.id,
                    })

                bulletin.line_ids.unlink()
                bulletin.write({
                    "line_ids": line_vals,
                    "date_generation": fields.Datetime.now(),
                })
                bulletins |= bulletin

            # Classement : calcule SEPAREMENT pour chaque classe, jamais
            # mélangé entre classes differentes. Le mode ex-aequo (eleves a
            # moyenne egale partagent le meme rang) peut etre desactive
            # dans Parametres > Ecole Primaire (Cameroun).
            sorted_bulletins = bulletins.sorted(key=lambda b: b.moyenne_generale, reverse=True)
            effectif = len(sorted_bulletins)
            moyenne_classe = (
                sum(sorted_bulletins.mapped("moyenne_generale")) / effectif if effectif else 0.0
            )
            use_ex_aequo = self.env["ir.config_parameter"].sudo().get_param(
                "edutek_primaire_cm.use_ex_aequo_ranking", "True")

            rang = 0
            previous_moyenne = None
            for index, bulletin in enumerate(sorted_bulletins, start=1):
                if use_ex_aequo in ("True", "1"):
                    if previous_moyenne is None or bulletin.moyenne_generale != previous_moyenne:
                        rang = index
                else:
                    rang = index
                bulletin.write({
                    "rang": rang,
                    "effectif_classe": effectif,
                    "moyenne_classe": moyenne_classe,
                    "appreciation": self._get_appreciation(bulletin.moyenne_generale),
                })
                previous_moyenne = bulletin.moyenne_generale

            all_bulletins |= bulletins

        if not all_bulletins:
            raise UserError(_(
                "Aucun bulletin genere : aucune classe selectionnee n'a "
                "cette periode parmi ses sequences applicables, ou les "
                "bulletins de sequence necessaires n'existent pas encore."))

        name = _("Bulletins")
        if skipped_classes or skipped_students:
            name = _(
                "Bulletins (%(classes)s classe(s) et %(students)s eleve(s) "
                "ignore(s) : periode non applicable ou donnees de sequence "
                "incompletes)",
                classes=skipped_classes, students=skipped_students,
            )

        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": "op.bulletin",
            "view_mode": "list,form",
            "domain": [("id", "in", all_bulletins.ids)],
            "context": {"search_default_group_classe": 1},
        }
