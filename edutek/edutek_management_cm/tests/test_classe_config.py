# -*- coding: utf-8 -*-
from odoo.addons.edutek_primaire_cm.tests.common import TestEdutekPrimaireCommon


class TestClasseConfigFields(TestEdutekPrimaireCommon):

    def test_classe_config_defaults(self):
        classe = self._create_classe()
        self.assertEqual(classe.moy_min_passage_trimestre, 10.0)
        self.assertEqual(classe.moy_min_passage_annee, 10.0)
        self.assertFalse(classe.bulletin_double)
        self.assertEqual(classe.determinant_reussite, "annuel")
        self.assertEqual(classe.type_bulletin, "defaut")

    def test_classe_config_bootstrap_lists_classe_and_its_fee_lines(self):
        classe = self._create_classe()
        bootstrap = self.env["op.classe"].get_classe_config_bootstrap()

        self.assertIn("classes", bootstrap)
        self.assertIn(classe.id, [c["id"] for c in bootstrap["classes"]])
        self.assertEqual(bootstrap["current_year_id"], self.academic_year.id)

        fee_lines_for_classe = [
            line for line in bootstrap["fee_lines"] if line["classe_id"][0] == classe.id]
        self.assertEqual(len(fee_lines_for_classe), 3)

        fee_type_names = {ft["name"] for ft in bootstrap["fee_types"]}
        self.assertIn("Inscription Scolarite", fee_type_names)

    def test_classe_config_bootstrap_selections_include_classe_levels(self):
        bootstrap = self.env["op.classe"].get_classe_config_bootstrap()
        level_values = {value for value, label in bootstrap["selections"]["level"]}
        self.assertIn("cm2", level_values)


class TestOpExam(TestEdutekPrimaireCommon):

    def test_exam_creation_minimal(self):
        classe = self._create_classe()
        exam = self.env["op.exam"].create({
            "name": "Concours d'entree en 6eme Test",
            "exam_type": "concours",
            "classe_id": classe.id,
            "academic_year_id": self.academic_year.id,
        })
        self.assertEqual(exam.exam_type, "concours")
        self.assertEqual(exam.classe_id, classe)
