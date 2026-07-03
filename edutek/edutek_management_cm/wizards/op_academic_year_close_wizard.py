# -*- coding: utf-8 -*-
import re

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

YEAR_NAME_RE = re.compile(r"^(\d{4})\s*-\s*(\d{4})$")


class OpAcademicYearCloseWizard(models.TransientModel):
    _name = "op.academic.year.close.wizard"
    _description = "Cloture d'annee academique (promotion des eleves)"

    academic_year_id = fields.Many2one(
        "op.academic.year", string="Annee a cloturer", required=True,
        domain=[("is_closed", "=", False)])
    next_year_name = fields.Char(string="Nom de l'annee suivante")
    next_year_start_date = fields.Date(string="Debut de l'annee suivante")
    next_year_end_date = fields.Date(string="Fin de l'annee suivante")
    preview = fields.Text(string="Apercu", compute="_compute_preview")

    @api.onchange("academic_year_id")
    def _onchange_academic_year_id(self):
        if not self.academic_year_id:
            return
        year = self.academic_year_id
        self.next_year_start_date = year.start_date + relativedelta(years=1)
        self.next_year_end_date = year.end_date + relativedelta(years=1)
        self.next_year_name = self._guess_next_year_name(year.name)

    @api.model
    def _guess_next_year_name(self, name):
        match = YEAR_NAME_RE.match((name or "").strip())
        if match:
            return "%s-%s" % (int(match.group(1)) + 1, int(match.group(2)) + 1)
        return name

    # ------------------------------------------------------------------
    # Apercu (lecture seule, aucune ecriture)
    # ------------------------------------------------------------------
    @api.depends("academic_year_id")
    def _compute_preview(self):
        for wizard in self:
            if not wizard.academic_year_id:
                wizard.preview = ""
                continue
            # academic_year_all=True : op.classe et op.student portent un
            # mixin qui filtre silencieusement toute recherche sans
            # condition explicite sur academic_year_id par l'annee
            # courante de l'utilisateur (cf. op_academic_year_filter_mixin.py).
            # classe.student_ids ne passe PAS de condition academic_year_id
            # explicite (juste classe_id in [...]), donc sans cet
            # echappatoire le mixin renverrait silencieusement aucun eleve
            # des qu'on cloture une annee qui n'est pas l'annee courante de
            # l'utilisateur.
            wizard = wizard.with_context(academic_year_all=True)
            classes = wizard.env["op.classe"].search(
                [("academic_year_id", "=", wizard.academic_year_id.id)],
                order="level_order, name")
            lines = []
            for classe in classes:
                students = classe.student_ids.filtered("active")
                if not students:
                    continue
                redoublants = students.filtered("redoublant")
                others = students - redoublants
                next_level = wizard._get_next_level(classe)
                dest = (wizard._guess_destination_name(classe, next_level)
                        if next_level else _("quittent l'ecole (fin de parcours)"))
                line = _("%(classe)s : %(count)d eleve(s) -> %(dest)s") % {
                    "classe": classe.name, "count": len(others), "dest": dest,
                }
                if redoublants:
                    line += _(" (+ %d redoublant(s) maintenu(s) au meme niveau)") % len(redoublants)
                lines.append(line)
            wizard.preview = "\n".join(lines) or _("Aucune classe active sur cette annee.")

    def _get_next_level(self, classe):
        """Premier niveau de sequence superieure a celui de `classe`, dans
        la meme section (anglophone/francophone/aucune) - ignore tout
        niveau de sequence superieure appartenant a une autre section,
        pour ne jamais faire basculer un eleve d'une section a l'autre."""
        Level = self.env["op.education.level"]
        current = Level.search([("code", "=", classe.level)], limit=1)
        if not current:
            return Level
        candidates = Level.search(
            [("sequence", ">", current.sequence)], order="sequence")
        for candidate in candidates:
            if candidate.section_id == current.section_id:
                return candidate
        return Level

    def _guess_destination_name(self, classe, next_level):
        old_level = self.env["op.education.level"].search(
            [("code", "=", classe.level)], limit=1)
        old_label = old_level.name if old_level else classe.level
        if old_label and classe.name.upper().startswith(old_label.upper()):
            suffix = classe.name[len(old_label):].strip()
            return ("%s %s" % (next_level.name, suffix)).strip()
        return "%s - %s" % (next_level.name, classe.name)

    # ------------------------------------------------------------------
    # Confirmation (ecritures)
    # ------------------------------------------------------------------
    def _get_or_create_next_year(self):
        self.ensure_one()
        if not self.next_year_name:
            raise UserError(_("Le nom de l'annee suivante est obligatoire."))
        Year = self.env["op.academic.year"]
        year = Year.search([("name", "=", self.next_year_name)], limit=1)
        if not year:
            year = Year.create({
                "name": self.next_year_name,
                "start_date": self.next_year_start_date,
                "end_date": self.next_year_end_date,
                "term_structure": self.academic_year_id.term_structure,
                "company_id": self.academic_year_id.company_id.id,
            })
        if not year.academic_term_ids:
            self._create_trimestre_sequence_terms(year)
        return year

    def _create_trimestre_sequence_terms(self, year):
        """Cree directement 3 Trimestres de 2 Sequences chacun pour `year` -
        remplace l'ancien appel a year.term_create() (logique generique
        jamais utilisee par cette ecole, qui ne produisait que des
        'Semester 1/2' a plat sans lien avec la structure reelle a 6
        sequences). Meme geometrie de dates que edutek_cameroun_system
        (op.academic.term._compute_trimestre_sequence_bounds), mais sans
        enregistrement ir.model.data : cette annee n'est pas geree par un
        module installable/desinstallable, donc pas de nettoyage a prevoir."""
        Term = self.env["op.academic.term"]
        bounds = Term._compute_trimestre_sequence_bounds(
            year.start_date, year.end_date)
        seq_counter = 0
        for t_index, trimestre_bounds in enumerate(bounds, start=1):
            trimestre = Term.create({
                "name": _("Trimestre %d") % t_index,
                "sequence": 100 + t_index,
                "academic_year_id": year.id,
                "term_start_date": trimestre_bounds["start"],
                "term_end_date": trimestre_bounds["end"],
            })
            for seq_bounds in trimestre_bounds["sequences"]:
                seq_counter += 1
                Term.create({
                    "name": _("Sequence %d") % seq_counter,
                    "sequence": seq_counter,
                    "academic_year_id": year.id,
                    "term_start_date": seq_bounds["start"],
                    "term_end_date": seq_bounds["end"],
                    "parent_term": trimestre.id,
                })

    def _get_or_create_classe(self, name, level_code, classe, next_year):
        Classe = self.env["op.classe"]
        dest = Classe.search([
            ("academic_year_id", "=", next_year.id), ("name", "=", name),
        ], limit=1)
        if not dest:
            dest = Classe.create({
                "name": name,
                "level": level_code,
                "academic_year_id": next_year.id,
                "sous_systeme": "anglophone" if classe.is_anglophone else "francophone",
                "company_id": classe.company_id.id,
            })
        self._copy_fee_lines(classe, dest)
        return dest

    def _copy_fee_lines(self, origin_classe, dest_classe):
        """Reporte les montants de frais de la classe d'origine sur la
        classe de destination : a la creation, celle-ci n'a que les frais
        generiques par defaut (montant 0, via op.classe.create() ->
        _ensure_default_fee_lines()) - sans ce report, aucun frais ne
        serait jamais facture aux eleves transferes (op.student._generate_
        class_fees() ignore silencieusement les lignes a montant <= 0)."""
        if origin_classe == dest_classe:
            return
        existing_by_type = {line.fee_type_id.id: line for line in dest_classe.fee_line_ids}
        Fee = self.env["op.classe.fee"]
        for line in origin_classe.fee_line_ids:
            dest_line = existing_by_type.get(line.fee_type_id.id)
            if dest_line:
                if dest_line.amount != line.amount:
                    dest_line.amount = line.amount
            else:
                Fee.create({
                    "classe_id": dest_classe.id,
                    "fee_type_id": line.fee_type_id.id,
                    "amount": line.amount,
                })

    def _get_or_create_destination_classe(self, classe, next_level, next_year):
        name = self._guess_destination_name(classe, next_level)
        return self._get_or_create_classe(name, next_level.code, classe, next_year)

    def _get_or_create_repeater_classe(self, classe, next_year):
        level = self.env["op.education.level"].search(
            [("code", "=", classe.level)], limit=1)
        label = level.name if level else classe.level
        name = _("%s - Redoublants") % label
        return self._get_or_create_classe(name, classe.level, classe, next_year)

    def action_confirm(self):
        self.ensure_one()
        if not self.academic_year_id:
            raise UserError(_("Veuillez choisir une annee a cloturer."))
        # academic_year_all=True : voir le commentaire dans _compute_preview -
        # sans cet echappatoire, classe.student_ids ci-dessous ne renverrait
        # silencieusement aucun eleve si l'annee courante de l'utilisateur
        # n'est pas celle qu'on cloture, et la cloture se terminerait "avec
        # succes" sans avoir rien transfere.
        self = self.with_context(academic_year_all=True)
        next_year = self._get_or_create_next_year()

        classes = self.env["op.classe"].search(
            [("academic_year_id", "=", self.academic_year_id.id)])
        for classe in classes:
            students = classe.student_ids.filtered("active")
            if not students:
                continue

            redoublants = students.filtered("redoublant")
            others = students - redoublants

            # Chaque eleve promu est CLONE sur un nouveau dossier (nouvelle
            # classe, nouveau matricule) plutot que transfere : le dossier
            # de cette annee n'est jamais modifie (ni sa classe, ni ses
            # frais/notes/bulletins) et reste consultable tel quel en
            # basculant sur cette annee academique (cf. op.student.
            # _clone_for_next_year). Seuls les eleves en fin de parcours
            # (pas de niveau suivant) sont archives, faute de dossier suivant.
            if redoublants:
                repeater_classe = self._get_or_create_repeater_classe(classe, next_year)
                for student in redoublants:
                    student._clone_for_next_year(repeater_classe.id)

            if others:
                next_level = self._get_next_level(classe)
                if next_level:
                    dest_classe = self._get_or_create_destination_classe(
                        classe, next_level, next_year)
                    for student in others:
                        student._clone_for_next_year(dest_classe.id)
                else:
                    others.write({"active": False})

        self.academic_year_id.is_closed = True

        return {
            "type": "ir.actions.act_window",
            "name": _("Classes de l'annee suivante"),
            "res_model": "op.classe",
            "view_mode": "list,form",
            "domain": [("academic_year_id", "=", next_year.id)],
        }
