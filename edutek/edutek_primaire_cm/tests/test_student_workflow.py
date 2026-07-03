# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError

from .common import TestEdutekPrimaireCommon


class TestStudentWorkflow(TestEdutekPrimaireCommon):

    def test_non_inscrit_by_default_without_paid_registration_fee(self):
        classe = self._create_classe()
        student = self._create_student(classe)
        self.assertEqual(student.inscription_state, "non_inscrit")

    def test_inscrit_once_registration_fee_is_paid(self):
        classe = self._create_classe()
        inscription_line = classe.fee_line_ids.filtered(
            lambda l: l.fee_type_id.name == "Inscription Scolarite")
        inscription_line.amount = 25000.0

        student = self._create_student(classe)
        fee = student.fee_ids[0]
        self.assertEqual(fee.amount, 25000.0)

        payment_register = self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=fee.move_id.ids,
        ).create({})
        payment_register._create_payments()

        student.invalidate_recordset(["inscription_state"])
        self.assertEqual(fee.move_id.payment_state, "paid")
        self.assertEqual(student.inscription_state, "inscrit")

    def test_student_cannot_be_deleted(self):
        classe = self._create_classe()
        student = self._create_student(classe)
        with self.assertRaises(UserError):
            student.unlink()

    def test_faculty_cannot_archive_student(self):
        classe = self._create_classe()
        student = self._create_student(classe)
        faculty_group = self.env.ref("edutek_core.group_op_faculty")
        faculty_user = self.env["res.users"].create({
            "name": "Enseignant Test",
            "login": "enseignant.test@example.com",
            "groups_id": [(6, 0, [faculty_group.id])],
        })
        with self.assertRaises(UserError):
            student.with_user(faculty_user).write({"active": False})
        self.assertTrue(student.active)

    def test_classe_cannot_be_deleted(self):
        classe = self._create_classe()
        with self.assertRaises(UserError):
            classe.unlink()

    def test_faculty_cannot_archive_classe(self):
        # Le groupe faculty n'a meme pas le droit d'ecriture ACL sur
        # op.classe (lecture seule) : AccessError avant meme d'atteindre la
        # restriction metier dans write(). Les deux sont une "non-archivage".
        classe = self._create_classe()
        faculty_group = self.env.ref("edutek_core.group_op_faculty")
        faculty_user = self.env["res.users"].create({
            "name": "Enseignant Test 2",
            "login": "enseignant.test2@example.com",
            "groups_id": [(6, 0, [faculty_group.id])],
        })
        with self.assertRaises((AccessError, UserError)):
            classe.with_user(faculty_user).write({"active": False})
        self.assertTrue(classe.active)
