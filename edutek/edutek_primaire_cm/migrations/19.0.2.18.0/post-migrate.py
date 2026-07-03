# -*- coding: utf-8 -*-
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

STAFF_TYPE_XMLIDS = {
    "non_enseignant": "edutek_primaire_cm.op_staff_type_non_enseignant",
    "enseignant_permanent": "edutek_primaire_cm.op_staff_type_enseignant_permanent",
    "enseignant_vacataire": "edutek_primaire_cm.op_staff_type_enseignant_vacataire",
}


def _column_exists(cr, table, column):
    cr.execute(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = %s AND column_name = %s",
        (table, column))
    return bool(cr.fetchone())


def _migrate_staff_type(cr, env):
    if not _column_exists(cr, "hr_employee", "staff_type_old_text"):
        return
    code_to_id = {}
    for code, xmlid in STAFF_TYPE_XMLIDS.items():
        record = env.ref(xmlid, raise_if_not_found=False)
        if record:
            code_to_id[code] = record.id

    cr.execute(
        "SELECT id, staff_type_old_text FROM hr_employee WHERE staff_type_old_text IS NOT NULL")
    rows = cr.fetchall()
    updated = 0
    for emp_id, code in rows:
        new_id = code_to_id.get(code)
        if new_id:
            cr.execute("UPDATE hr_employee SET staff_type = %s WHERE id = %s", (new_id, emp_id))
            updated += 1
    cr.execute('ALTER TABLE hr_employee DROP COLUMN staff_type_old_text')
    _logger.info(
        "edutek_primaire_cm: migrated staff_type for %s/%s employee(s).", updated, len(rows))


def _migrate_grade(cr, env):
    if not _column_exists(cr, "hr_employee", "grade_old_text"):
        return
    Grade = env["op.grade"]
    cr.execute(
        "SELECT DISTINCT grade_old_text FROM hr_employee "
        "WHERE grade_old_text IS NOT NULL AND btrim(grade_old_text) != ''")
    label_to_id = {}
    for (label,) in cr.fetchall():
        label = label.strip()
        record = Grade.search([("name", "=", label)], limit=1)
        if not record:
            record = Grade.create({"name": label})
        label_to_id[label] = record.id

    cr.execute(
        "SELECT id, grade_old_text FROM hr_employee "
        "WHERE grade_old_text IS NOT NULL AND btrim(grade_old_text) != ''")
    rows = cr.fetchall()
    updated = 0
    for emp_id, label in rows:
        new_id = label_to_id.get(label.strip())
        if new_id:
            cr.execute("UPDATE hr_employee SET grade = %s WHERE id = %s", (new_id, emp_id))
            updated += 1
    cr.execute('ALTER TABLE hr_employee DROP COLUMN grade_old_text')
    _logger.info(
        "edutek_primaire_cm: migrated grade for %s/%s employee(s), created %s op.grade record(s).",
        updated, len(rows), len(label_to_id))


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _migrate_staff_type(cr, env)
    _migrate_grade(cr, env)
