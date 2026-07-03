# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import _, fields, models

# Modeles dont le classe_id est cense etre fixe a la creation (cf. la
# correction apportee a op_student_fee.py / op_bulletin.py / op_student_mark.py
# / op_carnet.py / op_student_skill.py : ces champs etaient avant des
# related=student_id.classe_id, store=True, donc des "miroirs en direct" de
# la classe ACTUELLE de l'eleve - tout changement de classe_id sur l'eleve
# (promotion d'annee...) reecrivait silencieusement l'historique de TOUS ses
# frais/bulletins/notes/carnets/evaluations passes. Les deux derniers
# modeles (maternelle) sont optionnels : verifies via self.env avant usage,
# edutek_management_cm ne dependant pas formellement d'edutek_maternelle_cm.
_TARGET_MODELS = [
    ("op.student.fee", "Frais scolaires"),
    ("op.bulletin", "Bulletins"),
    ("op.student.mark", "Notes"),
    ("op.carnet", "Carnets (maternelle)"),
    ("op.student.skill", "Evaluations par competences (maternelle)"),
]


class OpHistoryRepairWizard(models.TransientModel):
    _name = "op.history.repair.wizard"
    _description = "Reparation des references de classe historiques corrompues"

    report = fields.Text(string="Rapport", readonly=True)

    def _history_map(self):
        """(student_id, academic_year_id) -> classe_id, d'apres
        op.student.enrollment.history - le seul endroit ou la classe d'un
        eleve pour une annee donnee est enregistree une fois et jamais
        recalculee par la suite, donc la seule source fiable pour reparer
        les autres modeles."""
        history_recs = self.env["op.student.enrollment.history"].with_context(
            academic_year_all=True).search([])
        return {
            (h.student_id.id, h.academic_year_id.id): h.classe_id.id
            for h in history_recs if h.academic_year_id
        }

    def _scan_model(self, model_name, history_map):
        if model_name not in self.env:
            return []
        Model = self.env[model_name].with_context(academic_year_all=True)
        records = Model.search([
            ("student_id", "!=", False), ("academic_year_id", "!=", False),
        ])
        mismatches = []
        for rec in records:
            correct_classe_id = history_map.get(
                (rec.student_id.id, rec.academic_year_id.id))
            current_classe_id = rec.classe_id.id if rec.classe_id else False
            if correct_classe_id and correct_classe_id != current_classe_id:
                mismatches.append((rec, correct_classe_id))
        return mismatches

    def _scan_all(self):
        history_map = self._history_map()
        results = []
        for model_name, label in _TARGET_MODELS:
            results.append((model_name, label, self._scan_model(model_name, history_map)))
        return results

    def action_analyze(self):
        """Lecture seule : ne corrige rien, affiche juste ce qui serait fait."""
        self.ensure_one()
        lines = []
        total = 0
        for model_name, label, mismatches in self._scan_all():
            total += len(mismatches)
            line = _("%(label)s : %(count)d enregistrement(s) a corriger") % {
                "label": label, "count": len(mismatches),
            }
            if mismatches:
                names = sorted({m[0].student_id.name for m in mismatches if m[0].student_id})[:8]
                line += " (%s%s)" % (", ".join(names), ", ..." if len(mismatches) > 8 else "")
            lines.append(line)
        self.report = "\n".join(lines) if total else _(
            "Aucune incoherence detectee : tout est deja correct.")
        return True

    def action_repair(self):
        self.ensure_one()
        lines = []
        total = 0
        for model_name, label, mismatches in self._scan_all():
            if not mismatches:
                continue
            groups = defaultdict(list)
            for rec, correct_classe_id in mismatches:
                groups[correct_classe_id].append(rec.id)
            Model = self.env[model_name]
            for classe_id, ids in groups.items():
                Model.browse(ids).write({"classe_id": classe_id})
            total += len(mismatches)
            lines.append(_("%(label)s : %(count)d enregistrement(s) corrige(s)") % {
                "label": label, "count": len(mismatches),
            })
        self.report = "\n".join(lines) if total else _(
            "Aucune incoherence detectee : rien a corriger.")
        return True
