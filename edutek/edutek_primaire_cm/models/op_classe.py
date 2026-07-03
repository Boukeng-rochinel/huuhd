# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OpClasse(models.Model):
    _name = "op.classe"
    _inherit = ["op.academic.year.filter.mixin"]
    _description = "Classe (Ecole Primaire)"
    _order = "academic_year_id desc, level_order, name"

    name = fields.Char(string="Nom", required=True)
    level = fields.Selection(
        selection="_selection_level", string="Niveau", required=True)
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique", required=True)
    matricule_prefix = fields.Char(
        string="Prefixe matricule",
        help="Prefixe utilise pour le matricule des eleves de cette classe "
             "(ex: 'CE2'). Si vide, le prefixe par defaut de l'ecole "
             "(Configuration > Fiche de l'ecole > Matricule) est utilise. "
             "Le numero de sequence reste commun a toute l'ecole.")
    teacher_id = fields.Many2one(
        "hr.employee", string="Maitre / Maitresse titulaire")
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True)

    student_ids = fields.One2many("op.student", "classe_id", string="Eleves")
    student_count = fields.Integer(compute="_compute_counts", string="Nb eleves")
    mark_count = fields.Integer(compute="_compute_counts", string="Nb notes")
    bulletin_count = fields.Integer(compute="_compute_counts", string="Nb bulletins")
    fee_unpaid_count = fields.Integer(compute="_compute_counts", string="Frais impayes")

    subject_line_ids = fields.One2many(
        "op.classe.subject", "classe_id", string="Programme (matieres / coefficients)")
    fee_line_ids = fields.One2many(
        "op.classe.fee", "classe_id", string="Frais configures")

    applicable_term_ids = fields.Many2many(
        "op.academic.term", string="Periodes (sequences) applicables",
        domain="[('academic_year_id', '=', academic_year_id), "
               "('child_term_ids', '=', False)]",
        help="Laisser vide = toutes les sequences de l'annee academique "
             "s'appliquent a cette classe (comportement par defaut). Ne "
             "remplir que pour une classe qui s'arrete plus tot que les "
             "autres (ex: une classe d'examen qui ne fait que 5 sequences "
             "au lieu de 6) - independant du flag 'Classe d'examen' : ce "
             "champ est la seule chose que la generation des notes/"
             "bulletins/frais consulte reellement.")

    level_order = fields.Integer(
        string="Ordre de niveau", compute="_compute_level_order", store=True)
    is_anglophone = fields.Boolean(
        string="Section anglophone", compute="_compute_is_anglophone", store=True,
        help="Determine la langue principale des documents officiels "
             "(certificats, attestations...) generes pour cette classe.")
    cycle = fields.Selection(
        selection="_selection_cycle", string="Cycle", compute="_compute_cycle", store=True)

    active = fields.Boolean(default=True)

    _unique_name_year = models.Constraint(
        "unique(name, academic_year_id)",
        "Une classe avec ce nom existe deja pour cette annee academique.")

    @api.model_create_multi
    def create(self, vals_list):
        classes = super().create(vals_list)
        classes._ensure_default_fee_lines()
        return classes

    def unlink(self):
        raise UserError(_(
            "Les classes ne peuvent pas etre supprimees, uniquement archivees "
            "(bouton Actions > Archiver)."))

    def _ensure_default_fee_lines(self):
        """Pre-remplit chaque classe de self avec les frais standards de
        l'ecole (Inscription Scolarite, Premiere/Deuxieme Tranche Pension),
        montant a 0 par defaut - un responsable (groupe Manager) ajuste
        ensuite le montant par classe ou retire une ligne depuis
        Configuration > Fiche de l'ecole > Classe. Idempotent : ne duplique
        jamais une ligne deja configuree."""
        fee_types = self.env["op.fee.type"]._get_or_create_default_fee_types()
        if not fee_types or not self:
            return
        existing = self.env["op.classe.fee"].search([
            ("classe_id", "in", self.ids), ("fee_type_id", "in", fee_types.ids),
        ])
        existing_pairs = {(l.classe_id.id, l.fee_type_id.id) for l in existing}
        vals_list = [
            {"classe_id": classe.id, "fee_type_id": fee_type.id, "amount": fee_type.amount}
            for classe in self
            for fee_type in fee_types
            if (classe.id, fee_type.id) not in existing_pairs
        ]
        if vals_list:
            self.env["op.classe.fee"].create(vals_list)

    @api.model
    def _ensure_default_fee_lines_all_classes(self):
        """Rejoue _ensure_default_fee_lines sur toutes les classes
        existantes - appele depuis une donnee XML (re-execute a chaque mise
        a jour du module) pour couvrir les classes creees avant l'ajout de
        cette fonctionnalite."""
        self.search([])._ensure_default_fee_lines()

    def write(self, vals):
        if "active" in vals and not self.env.user.has_group(
                "edutek_core.group_op_back_office_admin"):
            raise UserError(_(
                "Seuls les responsables (groupe Manager) peuvent archiver ou "
                "reactiver une classe."))
        return super().write(vals)

    def _get_applicable_terms(self):
        """Sequences (periodes-feuilles, jamais les Trimestres-conteneurs)
        qui s'appliquent reellement a cette classe : celles choisies
        manuellement dans applicable_term_ids, ou par defaut toutes les
        sequences de son annee academique si rien n'a ete restreint."""
        self.ensure_one()
        if self.applicable_term_ids:
            return self.applicable_term_ids
        return self.env["op.academic.term"].search([
            ("academic_year_id", "=", self.academic_year_id.id),
            ("child_term_ids", "=", False),
        ])

    @api.model
    def _selection_level(self):
        levels = self.env["op.education.level"].search([], order="sequence, name")
        return [(level.code, level.name) for level in levels]

    @api.model
    def _selection_cycle(self):
        cycles = self.env["op.education.cycle"].search([], order="sequence, name")
        return [(cycle.code, cycle.name) for cycle in cycles]

    def _education_levels_by_code(self):
        levels = self.env["op.education.level"].search([])
        return {level.code: level for level in levels}

    @api.depends("level")
    def _compute_level_order(self):
        by_code = self._education_levels_by_code()
        for rec in self:
            level = by_code.get(rec.level)
            rec.level_order = level.sequence if level else 99

    @api.depends("level")
    def _compute_cycle(self):
        by_code = self._education_levels_by_code()
        for rec in self:
            level = by_code.get(rec.level)
            rec.cycle = level.cycle_id.code if level and level.cycle_id else False

    @api.depends("level")
    def _compute_is_anglophone(self):
        by_code = self._education_levels_by_code()
        for rec in self:
            sous_systeme = getattr(rec, "sous_systeme", False)
            if sous_systeme:
                rec.is_anglophone = sous_systeme == "anglophone"
            else:
                level = by_code.get(rec.level)
                rec.is_anglophone = bool(
                    level and level.section_id and level.section_id.code == "anglophone")

    @api.depends("student_ids")
    def _compute_counts(self):
        for record in self:
            record.student_count = len(record.student_ids)
            record.mark_count = self.env["op.student.mark"].search_count(
                [("classe_id", "=", record.id)])
            record.bulletin_count = self.env["op.bulletin"].search_count(
                [("classe_id", "=", record.id)])
            record.fee_unpaid_count = self.env["op.student.fee"].search_count([
                ("classe_id", "=", record.id),
                ("state", "=", "posted"),
                ("payment_state", "in", ("not_paid", "partial")),
            ])

    def action_view_students(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Eleves",
            "res_model": "op.student",
            "view_mode": "list,form",
            "domain": [("classe_id", "=", self.id)],
            "context": {"default_classe_id": self.id},
        }

    def action_view_marks(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Notes",
            "res_model": "op.student.mark",
            "view_mode": "list",
            "domain": [("classe_id", "=", self.id)],
            "context": {"search_default_group_term": 1},
        }

    def action_view_bulletins(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Bulletins",
            "res_model": "op.bulletin",
            "view_mode": "kanban,list,form",
            "domain": [("classe_id", "=", self.id)],
            "context": {"search_default_group_term": 1},
        }

    def action_view_fees_unpaid(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Frais impayes",
            "res_model": "op.student.fee",
            "view_mode": "kanban,list,form",
            "domain": [
                ("classe_id", "=", self.id),
                ("state", "=", "posted"),
                ("payment_state", "in", ("not_paid", "partial")),
            ],
        }

    def action_open_mark_generate_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Saisir les notes",
            "res_model": "op.student.mark.generate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_classe_id": self.id},
        }

    def action_open_bulletin_generate_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Generer les bulletins",
            "res_model": "op.bulletin.generate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_classe_ids": [self.id]},
        }

    def action_open_fee_generate_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Generer des frais",
            "res_model": "op.student.fee.generate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_classe_ids": [self.id],
                "default_academic_year_id": self.academic_year_id.id,
            },
        }

    def action_open_student_list_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Liste des eleves",
            "res_model": "op.student.list.wizard",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_classe_ids": [self.id],
                "default_academic_year_id": self.academic_year_id.id,
            },
        }

    def action_open_insolvable_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Etat des insolvables",
            "res_model": "op.student.insolvable.wizard",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_classe_ids": [self.id],
                "default_academic_year_id": self.academic_year_id.id,
            },
        }


class OpClasseSubject(models.Model):
    _name = "op.classe.subject"
    _description = "Matiere du programme d'une classe"
    _order = "sequence, id"
    _rec_name = "subject_id"

    classe_id = fields.Many2one(
        "op.classe", string="Classe", required=True, ondelete="cascade")
    subject_id = fields.Many2one("op.subject", string="Matiere", required=True)
    coefficient = fields.Float(string="Coefficient", default=1.0, required=True)
    sequence = fields.Integer(string="Sequence", default=10)

    _unique_classe_subject = models.Constraint(
        "unique(classe_id, subject_id)",
        "Cette matiere figure deja dans le programme de cette classe.")
