##############################################################################
#
#    EduTek
#    Copyright (C) 2026 EduTek.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from . import controllers
from . import models
from . import wizard
from . import report

from odoo import api, SUPERUSER_ID

def _edutek_post_init(env):
    env['publisher_warranty.contract'].update_notification(cron_mode=True)
    # Activate French and English so the in-header language toggle works
    # immediately without the admin having to install languages manually.
    for lang_code in ("fr_FR", "en_US"):
        lang = env["res.lang"].with_context(active_test=False).search(
            [("code", "=", lang_code)], limit=1)
        if lang and not lang.active:
            lang.active = True
        if not lang:
            env["res.lang"]._activate_lang(lang_code)
