# -*- coding: utf-8 -*-
from odoo import api, fields, models

# Abreviations pour l'affichage secondaire
_LEVEL_ABBREV = {
    '6e': '6eme', '5e': '5eme', '4e': '4eme', '3e': '3eme',
    '2nde': '2nde', '1ere': '1ere', 'terminale': 'Tle',
    'form1': 'Form 1', 'form2': 'Form 2', 'form3': 'Form 3', 'form4': 'Form 4',
    'form5': 'Form 5', 'lower_sixth': 'L6', 'upper_sixth': 'U6',
}

# Labels courts pour l'affichage de la serie
_SERIE_DISPLAY = {
    'a4': 'A4', 'c': 'C', 'd': 'D', 'ti': 'TI', 'esp': 'ESP',
    'arts': 'Arts', 'sciences': 'Sciences', 'commercial': 'Commercial',
}

# Noms complets du niveau tels que l'utilisateur les a probablement saisis dans "name"
_LEVEL_STORED_NAMES = {
    '6e': '6eme', '5e': '5eme', '4e': '4eme', '3e': '3eme',
    '2nde': '2nde', '1ere': '1ere', 'terminale': 'Terminale',
    'form1': 'Form 1', 'form2': 'Form 2', 'form3': 'Form 3', 'form4': 'Form 4',
    'form5': 'Form 5', 'lower_sixth': 'Lower Sixth', 'upper_sixth': 'Upper Sixth',
}


def _extract_section(level, name):
    """Extrait la section (A, B, C...) du nom si le niveau y est deja inclus.
    Ex: level='terminale', name='Terminale A' -> 'A'
        level='2nde', name='2nde A' -> 'A'
        level='2nde', name='A' -> 'A' (deja propre)
    """
    name = name or ''
    stored = _LEVEL_STORED_NAMES.get(level, '')
    abbrev = _LEVEL_ABBREV.get(level, '')
    for prefix in (stored, abbrev):
        if prefix and name.lower().startswith(prefix.lower()):
            section = name[len(prefix):].strip()
            if section:
                return section
    return name.strip()


class OpClasse(models.Model):
    _inherit = "op.classe"

    sous_systeme = fields.Selection(
        selection="_selection_sous_systeme",
        string="Sous-systeme", default="francophone", required=True)

    @api.model
    def _selection_sous_systeme(self):
        sections = self.env["op.education.section"].search([], order="sequence, name")
        return [(section.code, section.name) for section in sections]

    @api.model
    def _selection_serie(self):
        series = self.env["op.education.serie"].search([], order="sequence, name")
        return [(serie.code, serie.name) for serie in series]

    def _compute_display_name(self):
        super()._compute_display_name()
        for rec in self:
            level_abbr = _LEVEL_ABBREV.get(rec.level, rec.level or '')
            section = _extract_section(rec.level, rec.name)
            if rec.serie:
                serie_disp = _SERIE_DISPLAY.get(rec.serie, rec.serie.upper())
                rec.display_name = f"{level_abbr} {serie_disp} - {section}"
            elif level_abbr:
                # College / Form 1-5 sans serie : "6eme A", "Form 3 B"
                rec.display_name = f"{level_abbr} {section}" if section != rec.name else rec.name

    serie = fields.Selection(selection="_selection_serie", string="Serie")
