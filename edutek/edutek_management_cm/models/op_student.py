# -*- coding: utf-8 -*-
from odoo import api, models

_REGISTRY_FIELDS = [
    "name", "gr_no", "enrollment_type", "classe_id", "gender", "birth_date",
    "age", "birth_place", "enfant_enseignant", "deficient_intellectuel", "observation",
    "inscription_state",
]


class OpStudent(models.Model):
    _inherit = "op.student"

    @api.model
    def _registry_domain(self, filters):
        filters = filters or {}
        domain = []
        if filters.get("search"):
            domain.append(("name", "ilike", filters["search"]))
        if filters.get("inscription_state") and filters["inscription_state"] != "tous":
            domain.append(("inscription_state", "=", filters["inscription_state"]))
        if filters.get("enrollment_type") and filters["enrollment_type"] != "tous":
            domain.append(("enrollment_type", "=", filters["enrollment_type"]))
        if filters.get("classe_id"):
            domain.append(("classe_id", "=", filters["classe_id"]))
        if filters.get("enfant_enseignant"):
            domain.append(("enfant_enseignant", "=", True))
        if filters.get("deficient_intellectuel"):
            domain.append(("deficient_intellectuel", "=", True))
        if filters.get("date_from"):
            domain.append(("create_date", ">=", filters["date_from"]))
        if filters.get("date_to"):
            domain.append(("create_date", "<=", filters["date_to"]))
        return domain

    @api.model
    def get_registry_page(self, filters, limit, offset):
        """Page de la grille 'Etats generaux' : eleves correspondant aux
        filtres, plus le suivi des pieces scolaires pour cette page
        uniquement (pour eviter de charger les pieces des 1000+ eleves)."""
        Student = self.with_context(academic_year_all=True)
        domain = self._registry_domain(filters)
        total = Student.search_count(domain)
        students = Student.search_read(domain, _REGISTRY_FIELDS, limit=limit, offset=offset, order="name")

        doc_types = self.env["op.school.document.type"].search_read([], ["name", "sequence"])
        student_ids = [s["id"] for s in students]
        documents = self.env["op.student.document"].search_read(
            [("student_id", "in", student_ids)], ["student_id", "document_type_id", "provided"])

        return {
            "total": total,
            "students": students,
            "document_types": doc_types,
            "documents": documents,
        }

    @api.model
    def get_effectif_par_classe(self, filters):
        Student = self.with_context(academic_year_all=True)
        domain = self._registry_domain(filters)
        groups = Student._read_group(domain, ["classe_id"], ["id:count"])
        return [{
            "classe_name": classe.display_name if classe else "Sans classe",
            "count": count,
        } for classe, count in groups]
