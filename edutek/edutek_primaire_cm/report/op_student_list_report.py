# -*- coding: utf-8 -*-
from itertools import groupby

from odoo import api, fields, models


class ReportStudentList(models.AbstractModel):
    _name = "report.edutek_primaire_cm.report_student_list_document"
    _description = "Liste des eleves - valeurs du rapport"

    @api.model
    def _get_report_values(self, docids, data=None):
        wizards = self.env["op.student.list.wizard"].browse(docids)
        wizard = wizards[:1]
        students = wizard._get_students() if wizard else self.env["op.student"]
        # Les colonnes "Classe" deviennent redondantes une fois les eleves
        # regroupes par classe (la classe est deja l'en-tete du groupe).
        columns = [c for c in (wizard._get_columns() if wizard else [])
                   if c[0] != "classe_id"]

        groups = []
        for classe, students_iter in groupby(students, key=lambda s: s.classe_id):
            group_students = self.env["op.student"].concat(*students_iter)
            groups.append({
                "classe": classe,
                "students": group_students,
                "males": len(group_students.filtered(lambda s: s.gender == "m")),
                "females": len(group_students.filtered(lambda s: s.gender == "f")),
            })

        now = fields.Datetime.context_timestamp(
            self, fields.Datetime.now()).strftime("%d/%m/%Y a %H:%M")
        return {
            "doc_ids": docids,
            "doc_model": "op.student.list.wizard",
            "docs": wizards,
            "company": self.env.company,
            "lang_en": False,
            "now": now,
            "groups": groups,
            "columns": columns,
            "list_type": wizard.list_type if wizard else "simple",
            "gender_labels": {"m": "Masculin", "f": "Feminin", "o": "Autre"},
        }
