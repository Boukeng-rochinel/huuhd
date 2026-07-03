# -*- coding: utf-8 -*-
from .common import TestEdutekPrimaireCommon


class TestBulletinGeneration(TestEdutekPrimaireCommon):

    def setUp(self):
        super().setUp()
        self.classe = self._create_classe()
        self.subject = self.env["op.subject"].create({
            "name": "Mathematiques Test",
            "code": "MATH-T",
        })
        self.classe_subject = self.env["op.classe.subject"].create({
            "classe_id": self.classe.id,
            "subject_id": self.subject.id,
            "coefficient": 2.0,
        })
        self.student_a = self._create_student(self.classe, last_name="A")
        self.student_b = self._create_student(self.classe, last_name="B")
        self.student_c = self._create_student(self.classe, last_name="C")
        for student, note in ((self.student_a, 18.0), (self.student_b, 10.0), (self.student_c, 18.0)):
            self.env["op.student.mark"].create({
                "student_id": student.id,
                "classe_subject_id": self.classe_subject.id,
                "academic_term_id": self.academic_term.id,
                "note": note,
            })

    def _generate(self):
        wizard = self.env["op.bulletin.generate.wizard"].create({
            "academic_term_id": self.academic_term.id,
            "classe_ids": [(6, 0, [self.classe.id])],
        })
        wizard.action_generate()
        return self.env["op.bulletin"].search([
            ("academic_term_id", "=", self.academic_term.id),
            ("classe_id", "=", self.classe.id),
        ])

    def _bulletin_of(self, bulletins, student):
        return bulletins.filtered(lambda b: b.student_id == student)

    def test_moyenne_equals_note_with_single_subject(self):
        bulletins = self._generate()
        bulletin_a = self._bulletin_of(bulletins, self.student_a)
        self.assertEqual(bulletin_a.moyenne_generale, 18.0)
        self.assertEqual(bulletin_a.effectif_classe, 3)

    def test_appreciation_thresholds(self):
        bulletins = self._generate()
        self.assertEqual(self._bulletin_of(bulletins, self.student_a).appreciation, "Excellent")
        self.assertEqual(self._bulletin_of(bulletins, self.student_b).appreciation, "Assez Bien")

    def test_ex_aequo_ranking_shares_rank_one(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "edutek_primaire_cm.use_ex_aequo_ranking", "True")
        bulletins = self._generate()
        self.assertEqual(self._bulletin_of(bulletins, self.student_a).rang, 1)
        self.assertEqual(self._bulletin_of(bulletins, self.student_c).rang, 1)
        self.assertEqual(self._bulletin_of(bulletins, self.student_b).rang, 3,
                          "Le rang 2 est consomme par l'ex-aequo, B doit etre 3e.")

    def test_ranking_without_ex_aequo_is_strictly_sequential(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "edutek_primaire_cm.use_ex_aequo_ranking", "False")
        bulletins = self._generate()
        ranks = sorted(bulletins.mapped("rang"))
        self.assertEqual(ranks, [1, 2, 3])

    def test_regenerating_bulletin_does_not_duplicate(self):
        self._generate()
        bulletins_again = self._generate()
        self.assertEqual(len(bulletins_again), 3)
        all_bulletins = self.env["op.bulletin"].search([
            ("academic_term_id", "=", self.academic_term.id),
            ("classe_id", "=", self.classe.id),
        ])
        self.assertEqual(len(all_bulletins), 3, "Regenerer ne doit pas creer de doublons.")
