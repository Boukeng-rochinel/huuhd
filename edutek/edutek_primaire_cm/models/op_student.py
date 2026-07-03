# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class OpStudent(models.Model):
    _inherit = ["op.student", "op.academic.year.filter.mixin"]

    classe_id = fields.Many2one("op.classe", string="Classe", tracking=True)
    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee academique",
        related="classe_id.academic_year_id", store=True, readonly=True)

    birth_place = fields.Char(string="Lieu de naissance")
    age = fields.Integer(string="Age", compute="_compute_age")
    ecole_origine = fields.Char(
        string="Ecole d'origine",
        help="Etablissement frequente par l'eleve avant son inscription ici "
             "(le cas echeant).")
    nationality = fields.Many2one(
        "res.country",
        default=lambda self: self.env.ref("base.cm", raise_if_not_found=False))

    is_new_student = fields.Boolean(string="Nouveau a l'ecole (manuel)")
    redoublant = fields.Boolean(string="Redoublant")
    deficient_intellectuel = fields.Boolean(string="Deficient intellectuel")
    demissionnaire = fields.Boolean(string="Demissionnaire")
    enfant_enseignant = fields.Boolean(string="Enfant enseignant")
    observation = fields.Text(string="Observation")

    parent1_name = fields.Char(string="Parent 1")
    parent1_phone = fields.Char(string="Telephone Parent 1")
    parent2_name = fields.Char(string="Parent 2")
    parent2_phone = fields.Char(string="Telephone Parent 2")

    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id)
    discount_amount = fields.Monetary(
        string="Reduction accordee", currency_field="currency_id",
        help="Montant fixe deduit de chaque frais genere pour cet eleve "
             "(generation automatique a l'affectation de classe, ou wizard "
             "de generation en masse).")
    fee_ids = fields.One2many(
        "op.student.fee", "student_id", string="Frais scolaires", copy=False)
    fee_total_due = fields.Monetary(
        string="Net a payer", compute="_compute_fee_totals", currency_field="currency_id")
    fee_total_paid = fields.Monetary(
        string="Deja paye", compute="_compute_fee_totals", currency_field="currency_id")
    fee_total_residual = fields.Monetary(
        string="Reste a payer", compute="_compute_fee_totals", currency_field="currency_id")
    previous_student_unpaid = fields.Monetary(
        string="Impaye annee precedente", currency_field="currency_id",
        compute="_compute_previous_student_unpaid",
        help="Montant reste a payer sur les frais de l'annee precedente "
             "de cet eleve. Affiche en rouge sur le bouton 'Annee precedente' "
             "si des frais sont encore en suspens.")

    history_ids = fields.One2many(
        "op.student.enrollment.history", "student_id",
        string="Historique d'inscription", copy=False)
    previous_student_id = fields.Many2one(
        "op.student", string="Dossier annee precedente", copy=False, index=True,
        help="Dossier de cet eleve pour l'annee academique precedente (cree "
             "par la cloture d'annee : Configuration > Cloturer une annee "
             "academique). Ce dossier-ci ne contient que les infos "
             "personnelles et la nouvelle classe - aucune note, aucun "
             "bulletin, aucun frais n'est jamais reporte d'une annee a "
             "l'autre. Basculer sur l'annee academique precedente (en haut "
             "a droite) pour consulter ce dossier tel qu'il etait alors.")
    next_student_ids = fields.One2many(
        "op.student", "previous_student_id", string="Dossier(s) annee(s) suivante(s)")
    inscription_state = fields.Selection(
        [("inscrit", "Inscrit"), ("non_inscrit", "Non Inscrit")],
        string="Statut d'inscription",
        compute="_compute_inscription_state",
        search="_search_inscription_state")
    enrollment_type = fields.Selection(
        [("nouveau", "Nouveau"), ("ancien", "Ancien")],
        string="Statut eleve",
        compute="_compute_enrollment_type",
        search="_search_enrollment_type")

    # Remplace _unique_gr_no (unique(gr_no) tout court, defini dans
    # edutek_core) : le matricule est l'identite permanente de l'eleve d'une
    # annee a l'autre (carte scolaire, dossiers d'examens officiels...), donc
    # _clone_for_next_year() le reprend tel quel sur le nouveau dossier - il
    # ne doit rester unique que PARMI les dossiers d'une meme annee
    # academique, jamais entre annees. cf. migrations/19.0.2.22.0 pour le
    # remplacement de la contrainte SQL deja en base (Odoo ne le fait jamais
    # automatiquement pour une contrainte de meme nom).
    _unique_gr_no = models.Constraint(
        "unique(gr_no, academic_year_id)",
        "Le matricule doit etre unique pour une meme annee academique !")

    @api.depends("birth_date")
    def _compute_age(self):
        today = fields.Date.today()
        for record in self:
            if not record.birth_date:
                record.age = 0
                continue
            birth = record.birth_date
            years = today.year - birth.year
            if (today.month, today.day) < (birth.month, birth.day):
                years -= 1
            record.age = years

    @api.depends("fee_ids.amount", "fee_ids.amount_residual", "fee_ids.state",
                 "fee_ids.academic_year_id", "classe_id.academic_year_id")
    def _compute_fee_totals(self):
        for record in self:
            year = record.classe_id.academic_year_id
            fees = record.fee_ids.filtered(
                lambda f: f.state == "posted" and (
                    not year or f.academic_year_id == year))
            record.fee_total_due = sum(fees.mapped("amount"))
            record.fee_total_residual = sum(fees.mapped("amount_residual"))
            record.fee_total_paid = record.fee_total_due - record.fee_total_residual

    @api.depends(
        "classe_id.academic_year_id", "fee_ids.state", "fee_ids.payment_state",
        "fee_ids.academic_year_id", "fee_ids.fee_type_id.is_registration_fee")
    def _compute_inscription_state(self):
        for record in self:
            year = record.classe_id.academic_year_id
            if not year:
                record.inscription_state = "non_inscrit"
                continue
            paid_registration = record.fee_ids.filtered(
                lambda f: f.fee_type_id.is_registration_fee
                and f.academic_year_id == year
                and f.payment_state == "paid")
            record.inscription_state = "inscrit" if paid_registration else "non_inscrit"

    @api.depends(
        "previous_student_id",
        "previous_student_id.fee_ids.state",
        "previous_student_id.fee_ids.payment_state",
        "previous_student_id.fee_ids.amount_residual")
    def _compute_previous_student_unpaid(self):
        for record in self:
            prev = record.previous_student_id
            if not prev:
                record.previous_student_unpaid = 0.0
                continue
            unpaid_fees = prev.fee_ids.filtered(
                lambda f: f.state == "posted"
                and f.payment_state not in ("paid", "reversed"))
            record.previous_student_unpaid = sum(unpaid_fees.mapped("amount_residual"))

    def _search_inscription_state(self, operator, value):
        if operator == "=":
            wants_inscrit = value == "inscrit"
        elif operator == "!=":
            wants_inscrit = value != "inscrit"
        else:
            raise NotImplementedError(
                _("Operateur de recherche non supporte pour le statut d'inscription."))
        current_year = self.env.user.current_academic_year_id
        if not current_year:
            return [("id", "in", [])] if wants_inscrit else []
        paid_student_ids = self.env["op.student.fee"].search([
            ("fee_type_id.is_registration_fee", "=", True),
            ("academic_year_id", "=", current_year.id),
            ("payment_state", "=", "paid"),
        ]).student_id.ids
        inscrit_ids = self.search([
            ("classe_id.academic_year_id", "=", current_year.id),
            ("id", "in", paid_student_ids),
        ]).ids
        if wants_inscrit:
            return [("id", "in", inscrit_ids)]
        return [("id", "not in", inscrit_ids)]

    @api.depends("previous_student_id")
    def _compute_enrollment_type(self):
        for record in self:
            record.enrollment_type = "ancien" if record.previous_student_id else "nouveau"

    def _search_enrollment_type(self, operator, value):
        if operator == "=":
            wants_ancien = value == "ancien"
        elif operator == "!=":
            wants_ancien = value != "ancien"
        else:
            raise NotImplementedError(
                _("Operateur de recherche non supporte pour le statut eleve."))
        return [("previous_student_id", "!=" if wants_ancien else "=", False)]

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.company.matricule_auto_assign:
            Classe = self.env["op.classe"]
            for vals in vals_list:
                if not vals.get("gr_no"):
                    classe = Classe.browse(vals["classe_id"]) if vals.get("classe_id") else False
                    vals["gr_no"] = self.env.company._next_matricule(classe)
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            if vals.get("classe_id"):
                record._snapshot_enrollment()
                record._generate_class_fees()
        return records

    def write(self, vals):
        if "active" in vals and not self.env.user.has_group(
                "edutek_core.group_op_back_office_admin"):
            raise UserError(_(
                "Seuls les responsables (groupe Manager) peuvent archiver ou "
                "reactiver un eleve."))
        res = super().write(vals)
        if vals.get("classe_id"):
            for record in self:
                record._snapshot_enrollment()
                if not self.env.context.get("skip_fee_generation"):
                    record._generate_class_fees()
        return res

    def unlink(self):
        raise UserError(_(
            "Les eleves ne peuvent pas etre supprimes, uniquement archives "
            "(bouton Actions > Archiver)."))

    def action_change_classe(self):
        self.ensure_one()
        if not self.classe_id:
            raise UserError(_(
                "L'élève n'a pas encore de classe assignée. "
                "Utilisez le champ Classe directement."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Transfert / Redoublement — %s") % self.name,
            "res_model": "op.student.change.classe.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_student_id": self.id,
            },
        }

    def action_view_fees(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Frais scolaires"),
            "res_model": "op.student.fee",
            "view_mode": "list,form",
            "domain": [("student_id", "=", self.id)],
            "context": {"default_student_id": self.id},
        }

    def action_view_previous_student(self):
        self.ensure_one()
        if not self.previous_student_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("Dossier annee precedente"),
            "res_model": "op.student",
            "view_mode": "form",
            "res_id": self.previous_student_id.id,
        }

    def action_view_next_students(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Dossier(s) annee(s) suivante(s)"),
            "res_model": "op.student",
            "view_mode": "list,form",
            "domain": [("previous_student_id", "=", self.id)],
        }

    def action_view_lifecycle(self):
        """Tous les dossiers (toutes annees) partageant ce matricule - plus
        direct que de remonter/descendre la chaine previous_student_id /
        next_student_ids lien par lien, et insensible a un chainon qui
        aurait pu manquer (dossier cree hors cloture d'annee, par exemple)."""
        self.ensure_one()
        if not self.gr_no:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": _("Parcours complet (toutes annees) - %s") % self.gr_no,
            "res_model": "op.student",
            "view_mode": "list,form",
            "domain": [("gr_no", "=", self.gr_no)],
            "context": {"academic_year_all": 1},
        }

    def _generate_class_fees(self):
        """Affecte automatiquement a l'eleve chaque frais configure sur sa
        classe (montant > 0 : une ligne a 0 est consideree comme pas encore
        definie par l'administrateur et ignoree), pour l'annee academique de
        cette classe, et le comptabilise immediatement (facture postee).
        N'affecte jamais deux fois le meme type de frais pour la meme annee
        (idempotent). Les frais annules sont ignores et peuvent etre regeneres."""
        self.ensure_one()
        if not self.classe_id or not self.classe_id.fee_line_ids:
            return
        Fee = self.env["op.student.fee"]
        year_id = self.classe_id.academic_year_id.id
        existing_type_ids = set(Fee.search([
            ("student_id", "=", self.id),
            ("academic_year_id", "=", year_id),
            ("state", "!=", "cancelled"),
        ]).fee_type_id.ids)
        for line in self.classe_id.fee_line_ids:
            if line.amount <= 0:
                continue
            if line.fee_type_id.id in existing_type_ids:
                continue
            fee = Fee.create({
                "student_id": self.id,
                "fee_type_id": line.fee_type_id.id,
                "academic_year_id": year_id,
                "amount": max(line.amount - self.discount_amount, 0.0),
            })
            fee.action_post()

    def _snapshot_enrollment(self):
        self.ensure_one()
        if not self.classe_id:
            return
        history = self.env["op.student.enrollment.history"].search([
            ("student_id", "=", self.id),
            ("academic_year_id", "=", self.classe_id.academic_year_id.id),
        ], limit=1)
        if history:
            if history.classe_id != self.classe_id:
                history.classe_id = self.classe_id
        else:
            self.env["op.student.enrollment.history"].create({
                "student_id": self.id,
                "classe_id": self.classe_id.id,
            })

    def _clone_for_next_year(self, classe_id, **extra_vals):
        """Clone ce dossier pour l'annee academique suivante : un tout
        nouveau dossier (et un tout nouveau contact, cf. _inherits sur
        res.partner) reprenant les infos personnelles de l'eleve - y compris
        son matricule, identite permanente de l'eleve d'une annee a l'autre
        (cf. _unique_gr_no, unique par annee academique plutot que globalement
        unique) - avec sa nouvelle classe, mais jamais ses frais, notes ou
        bulletins (deja exclus via copy=False sur fee_ids/history_ids). Ce
        dossier-ci n'est jamais modifie : il reste consultable tel quel en
        basculant sur son annee academique."""
        self.ensure_one()
        vals = {
            "classe_id": classe_id,
            "previous_student_id": self.id,
            "redoublant": False,
            "gr_no": self.gr_no,
        }
        vals.update(extra_vals)
        return self.with_context(edutek_allow_student_copy=True).copy(vals)
