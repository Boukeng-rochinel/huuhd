# -*- coding: utf-8 -*-
from odoo.addons.edutek_primaire_cm.tests.common import TestEdutekPrimaireCommon


class TestSecondaireClasseDisplayName(TestEdutekPrimaireCommon):
    """display_name reconstruit "Niveau (Serie) - Section" a partir du nom
    saisi tel quel (ex: 'Terminale A') : ce sont des regles d'extraction de
    texte fragiles, exactement le genre de logique qui merite un test."""

    def test_francophone_lycee_without_serie(self):
        classe = self.env["op.classe"].create({
            "name": "Terminale A",
            "level": "terminale",
            "sous_systeme": "francophone",
            "academic_year_id": self.academic_year.id,
        })
        self.assertEqual(classe.display_name, "Tle A")

    def test_francophone_lycee_with_serie(self):
        classe = self.env["op.classe"].create({
            "name": "Terminale A",
            "level": "terminale",
            "sous_systeme": "francophone",
            "serie": "c",
            "academic_year_id": self.academic_year.id,
        })
        self.assertEqual(classe.display_name, "Tle C - A")

    def test_anglophone_form_without_serie(self):
        classe = self.env["op.classe"].create({
            "name": "Form 3 B",
            "level": "form3",
            "sous_systeme": "anglophone",
            "academic_year_id": self.academic_year.id,
        })
        self.assertEqual(classe.display_name, "Form 3 B")

    def test_anglophone_a_level_with_serie(self):
        classe = self.env["op.classe"].create({
            "name": "Lower Sixth A",
            "level": "lower_sixth",
            "sous_systeme": "anglophone",
            "serie": "sciences",
            "academic_year_id": self.academic_year.id,
        })
        self.assertEqual(classe.display_name, "L6 Sciences - A")

    def test_college_level_is_anglophone_flag(self):
        classe = self.env["op.classe"].create({
            "name": "Form 1 A",
            "level": "form1",
            "sous_systeme": "anglophone",
            "academic_year_id": self.academic_year.id,
        })
        self.assertTrue(classe.is_anglophone)
        self.assertEqual(classe.cycle, "secondaire")


class TestSecondaireBulletinLang(TestEdutekPrimaireCommon):

    def _make_bulletin(self, sous_systeme):
        classe = self.env["op.classe"].create({
            "name": "Terminale A",
            "level": "terminale",
            "sous_systeme": sous_systeme,
            "academic_year_id": self.academic_year.id,
        })
        student = self._create_student(classe)
        return self.env["op.bulletin"].create({
            "student_id": student.id,
            "academic_term_id": self.academic_term.id,
        })

    def test_anglophone_classe_forces_english_report_lang(self):
        bulletin = self._make_bulletin("anglophone")
        action = bulletin.action_print_bulletin()
        self.assertEqual(action.get("context", {}).get("lang"), "en_US")

    def test_francophone_classe_does_not_force_english(self):
        bulletin = self._make_bulletin("francophone")
        action = bulletin.action_print_bulletin()
        self.assertNotEqual(action.get("context", {}).get("lang"), "en_US")
