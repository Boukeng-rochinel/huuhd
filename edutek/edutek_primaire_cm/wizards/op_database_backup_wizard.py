# -*- coding: utf-8 -*-
import base64
import io

from odoo import fields, models
from odoo.service import db as odoo_db


class OpDatabaseBackupWizard(models.TransientModel):
    _name = "op.database.backup.wizard"
    _description = "Sauvegarde complete de la base de donnees"

    master_pwd = fields.Char(
        string="Mot de passe maitre", required=True,
        help="Le mot de passe maitre du serveur Odoo (le meme que celui du "
             "Gestionnaire de bases de donnees). Independant des comptes "
             "utilisateurs : il protege la sauvegarde, qui contient les "
             "donnees de tous les utilisateurs.")
    backup_format = fields.Selection(
        [("zip", "Complete (donnees + fichiers joints)"),
         ("dump", "Base de donnees seulement (sans fichiers joints)")],
        string="Format", default="zip", required=True)

    file_data = fields.Binary(string="Fichier", readonly=True)
    file_name = fields.Char(string="Nom du fichier", readonly=True)

    def action_backup(self):
        self.ensure_one()
        odoo_db.check_super(self.master_pwd)

        output = io.BytesIO()
        odoo_db.dump_db(self.env.cr.dbname, output, self.backup_format)
        output.seek(0)

        extension = "zip" if self.backup_format == "zip" else "dump"
        fname = "backup_%s_%s.%s" % (
            self.env.cr.dbname, fields.Date.today().strftime("%Y%m%d"), extension)
        self.write({
            "file_data": base64.b64encode(output.read()),
            "file_name": fname,
        })
        output.close()

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s/%s/file_data/%s?download=true"
                   % (self._name, self.id, self.file_name),
            "target": "self",
        }
