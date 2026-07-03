# Part of EduTek. See LICENSE file for full copyright & licensing details.

##############################################################################
#
#    EduTek
#    Copyright (C) 2026 EduTek.
#
##############################################################################

from datetime import timedelta

from odoo import api, fields, models


class OpAcademicTerm(models.Model):

    _name = 'op.academic.term'
    _description = "Academic Term"
    _order = "academic_year_id, sequence, term_start_date"

    name = fields.Char('Name', required=True)
    sequence = fields.Integer(
        string="Ordre", default=1,
        help="Position de cette periode parmi ses semblables (1, 2, 3...), "
             "independante de son libelle (Trimestre, Sequence...). Permet aux "
             "filtres/rapports de cibler 'la 1ere periode' sans dependre du nom "
             "exact utilise par chaque ecole. Convention de ce depot : les "
             "periodes-feuilles (Sequence) gardent une numerotation 1..N "
             "propre a l'annee ; les periodes-conteneurs (Trimestre) sont "
             "numerotees a partir de 101 pour ne jamais entrer en collision "
             "avec les filtres 'Sequence N' deja en place.")
    term_start_date = fields.Date('Start Date', required=True)
    term_end_date = fields.Date('End Date', required=True)
    academic_year_id = fields.Many2one(
        'op.academic.year', 'Academic Year', required=True)
    parent_term = fields.Many2one('op.academic.term', 'Parent Term')
    child_term_ids = fields.One2many(
        'op.academic.term', 'parent_term', string='Sous-periodes',
        help="Ex: les 2 Sequences d'un Trimestre. Une periode avec des "
             "sous-periodes est traitee comme un conteneur (Trimestre) : on "
             "n'y saisit jamais de notes directement, seulement un bulletin "
             "agrege a partir de ses sous-periodes.")
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id)

    _unique_name = models.Constraint('UNIQUE(name, academic_year_id)',
                                     'Name must be unique per Academic Year.')
    # Pas de contrainte d'unicite sur les dates : un Trimestre partage
    # delibrement sa date de debut avec sa 1ere Sequence et sa date de fin
    # avec sa derniere Sequence (son intervalle EST l'union de ses
    # sous-periodes), donc les dates se recoupent par construction entre
    # parent et enfants.

    @api.model
    def _compute_trimestre_sequence_bounds(
            self, start_date, end_date, n_trimestres=3, sequences_per_trimestre=2):
        """Decoupe [start_date, end_date] en `n_trimestres` trimestres
        consecutifs de longueur egale, chacun subdivise a son tour en
        `sequences_per_trimestre` sequences consecutives de longueur egale
        (le dernier sous-decoupage de chaque niveau recupere les jours
        restants). Ne cree aucun enregistrement : renvoie juste la
        geometrie des dates, pour que chaque module appelant cree ses
        propres op.academic.term avec sa propre logique (xmlid ou pas).

        Renvoie une liste de dicts {start, end, sequences: [{start, end}, ...]}.
        """
        total_days = (end_date - start_date).days + 1
        chunk = total_days // n_trimestres
        bounds = []
        cursor = start_date
        for t_index in range(n_trimestres):
            t_end = end_date if t_index == n_trimestres - 1 else (
                cursor + timedelta(days=chunk - 1))
            seq_total_days = (t_end - cursor).days + 1
            seq_chunk = seq_total_days // sequences_per_trimestre
            seq_cursor = cursor
            sequences = []
            for s_index in range(sequences_per_trimestre):
                s_end = t_end if s_index == sequences_per_trimestre - 1 else (
                    seq_cursor + timedelta(days=seq_chunk - 1))
                sequences.append({'start': seq_cursor, 'end': s_end})
                seq_cursor = s_end + timedelta(days=1)
            bounds.append({'start': cursor, 'end': t_end, 'sequences': sequences})
            cursor = t_end + timedelta(days=1)
        return bounds
