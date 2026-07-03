# -*- coding: utf-8 -*-
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _snapshot(history_model, student, classe):
    if not classe or not classe.academic_year_id:
        return
    existing = history_model.search([
        ("student_id", "=", student.id),
        ("academic_year_id", "=", classe.academic_year_id.id),
    ], limit=1)
    if not existing:
        history_model.create({"student_id": student.id, "classe_id": classe.id})


def migrate(cr, version):
    """Seed op.student.enrollment.history so 'Ancien/Nouveau' is meaningful
    immediately after upgrade, instead of only going forward.

    Source 1: every student's current classe_id assignment.
    Source 2 (best effort): mail.tracking.value entries for past classe_id
    changes, since that field has tracking=True and is the only place past
    assignments survive (there is no dedicated enrollment-history model
    before this migration).
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    Student = env["op.student"].with_context(academic_year_all=1)
    History = env["op.student.enrollment.history"]
    Classe = env["op.classe"]

    students = Student.search([("classe_id", "!=", False)])
    for student in students:
        _snapshot(History, student, student.classe_id)

    tracking_values = env["mail.tracking.value"].search([
        ("field_id.model", "=", "op.student"),
        ("field_id.name", "=", "classe_id"),
    ])
    for tracking in tracking_values:
        student_id = tracking.mail_message_id.res_id
        if not student_id:
            continue
        student = Student.browse(student_id)
        if not student.exists():
            continue
        for classe_id in (tracking.old_value_integer, tracking.new_value_integer):
            if not classe_id:
                continue
            classe = Classe.browse(classe_id)
            if classe.exists():
                _snapshot(History, student, classe)

    _logger.info(
        "edutek_primaire_cm: backfilled %s enrollment history record(s).",
        History.search_count([]))
