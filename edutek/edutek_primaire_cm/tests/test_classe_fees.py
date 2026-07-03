# -*- coding: utf-8 -*-
from odoo.exceptions import UserError

from .common import TestEdutekPrimaireCommon


class TestClasseFees(TestEdutekPrimaireCommon):

    def test_new_classe_is_seeded_with_three_default_fee_lines(self):
        classe = self._create_classe()
        self.assertEqual(len(classe.fee_line_ids), 3)
        names = set(classe.fee_line_ids.fee_type_id.mapped("name"))
        self.assertEqual(names, {
            "Inscription Scolarite",
            "Premiere Tranche Pension",
            "Deuxieme Tranche Pension",
        })
        # Montant par defaut a 0 : a configurer par classe par un responsable.
        self.assertTrue(all(line.amount == 0 for line in classe.fee_line_ids))

    def test_inscription_fee_type_drives_registration_flag(self):
        classe = self._create_classe()
        inscription = classe.fee_line_ids.fee_type_id.filtered(
            lambda f: f.name == "Inscription Scolarite")
        self.assertTrue(inscription.is_registration_fee)
        others = classe.fee_line_ids.fee_type_id - inscription
        self.assertFalse(any(others.mapped("is_registration_fee")))

    def test_seeding_is_idempotent_on_second_classe(self):
        self._create_classe("CM2 A Test")
        fee_type_count = self.env["op.fee.type"].search_count([
            ("name", "in", [
                "Inscription Scolarite", "Premiere Tranche Pension",
                "Deuxieme Tranche Pension",
            ]),
            ("company_id", "=", self.company.id),
        ])
        self._create_classe("CM2 B Test")
        fee_type_count_after = self.env["op.fee.type"].search_count([
            ("name", "in", [
                "Inscription Scolarite", "Premiere Tranche Pension",
                "Deuxieme Tranche Pension",
            ]),
            ("company_id", "=", self.company.id),
        ])
        self.assertEqual(fee_type_count, 3)
        self.assertEqual(fee_type_count_after, 3, "Aucun doublon de type de frais a la 2e classe.")

    def test_backfill_all_classes_does_not_duplicate_existing_lines(self):
        classe = self._create_classe()
        self.env["op.classe"]._ensure_default_fee_lines_all_classes()
        self.assertEqual(len(classe.fee_line_ids), 3)

    def test_zero_amount_fee_line_is_skipped_not_crashed(self):
        """Regression : une ligne a 0 (valeur par defaut a la creation de la
        classe) ne doit jamais faire planter l'inscription d'un eleve."""
        classe = self._create_classe()
        student = self._create_student(classe)
        self.assertFalse(student.fee_ids, "Aucune ligne a 0 ne doit generer de frais.")

    def test_positive_amount_fee_line_generates_posted_invoice(self):
        classe = self._create_classe()
        inscription_line = classe.fee_line_ids.filtered(
            lambda l: l.fee_type_id.name == "Inscription Scolarite")
        inscription_line.amount = 25000.0

        student = self._create_student(classe)

        self.assertEqual(len(student.fee_ids), 1)
        fee = student.fee_ids[0]
        self.assertEqual(fee.state, "posted")
        self.assertEqual(fee.amount, 25000.0)
        self.assertTrue(fee.move_id)
        self.assertEqual(fee.move_id.state, "posted")

    def test_changing_classe_does_not_duplicate_same_fee_type(self):
        classe_a = self._create_classe("CM2 A Test")
        classe_a.fee_line_ids.filtered(
            lambda l: l.fee_type_id.name == "Inscription Scolarite").amount = 25000.0
        classe_b = self._create_classe("CM2 B Test")
        classe_b.fee_line_ids.filtered(
            lambda l: l.fee_type_id.name == "Inscription Scolarite").amount = 30000.0

        student = self._create_student(classe_a)
        self.assertEqual(len(student.fee_ids), 1)

        student.classe_id = classe_b.id
        self.assertEqual(
            len(student.fee_ids), 1,
            "Meme type de frais deja facture cette annee : pas de 2e facture au changement de classe.")

    def test_classe_fee_unique_constraint(self):
        classe = self._create_classe()
        fee_type = classe.fee_line_ids[0].fee_type_id
        with self.assertRaises(Exception):
            self.env["op.classe.fee"].create({
                "classe_id": classe.id,
                "fee_type_id": fee_type.id,
                "amount": 1000.0,
            })

    def test_student_fee_cannot_post_with_non_positive_amount(self):
        classe = self._create_classe()
        student = self._create_student(classe)
        fee = self.env["op.student.fee"].create({
            "student_id": student.id,
            "fee_type_id": classe.fee_line_ids[0].fee_type_id.id,
            "academic_year_id": self.academic_year.id,
            "amount": 0.0,
        })
        with self.assertRaises(UserError):
            fee.action_post()
