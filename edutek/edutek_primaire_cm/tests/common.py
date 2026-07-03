# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase


class TestEdutekPrimaireCommon(TransactionCase):
    """Fixtures auto-suffisantes (aucune dependance aux donnees de demo) pour
    les tests du cycle eleve : annee academique, compte de produit, et
    raccourcis pour creer classe/eleve avec le minimum de champs requis."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.income_account = cls.env["account.account"].create({
            "code": "70999",
            "name": "Produits Test",
            "account_type": "income",
            "company_ids": [(6, 0, [cls.company.id])],
        })
        cls.academic_year = cls.env["op.academic.year"].create({
            "name": "2025/2026 Test",
            "start_date": "2025-09-01",
            "end_date": "2026-07-31",
        })
        cls.academic_term = cls.env["op.academic.term"].create({
            "name": "Trimestre 1 Test",
            "term_start_date": "2025-09-01",
            "term_end_date": "2025-12-20",
            "academic_year_id": cls.academic_year.id,
        })
        # current_academic_year_id n'a aucune valeur par defaut (seulement
        # renseigne par le widget systray au premier chargement de page) :
        # sans cette ligne, op.academic.year.filter.mixin et
        # _compute_inscription_state se comportent tous deux comme si
        # aucune annee n'etait jamais "en cours", et inscription_state reste
        # bloque a 'non_inscrit' quoi qu'on fasse.
        cls.env.user.current_academic_year_id = cls.academic_year.id

    def _create_classe(self, name="CM2 Test", level="cm2"):
        return self.env["op.classe"].create({
            "name": name,
            "level": level,
            "academic_year_id": self.academic_year.id,
        })

    def _create_student(self, classe, first_name="Jean", last_name="Test"):
        return self.env["op.student"].create({
            "first_name": first_name,
            "last_name": last_name,
            "classe_id": classe.id,
        })
