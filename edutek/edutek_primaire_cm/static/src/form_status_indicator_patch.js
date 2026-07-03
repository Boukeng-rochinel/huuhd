/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormStatusIndicator } from "@web/views/form/form_status_indicator/form_status_indicator";

// Modeles EduTek : sur ces ecrans le bouton Enregistrer/Annuler est TOUJOURS
// visible (meme sans modifications en attente) pour que l'utilisateur puisse a
// tout moment sauvegarder ou annuler. En mode "sauvegarde" les boutons sont
// affiches a 50% d'opacite pour signaler "tout est enregistre". Partout
// ailleurs dans le backend le comportement standard d'Odoo est inchange.
const SIS_MODEL_PREFIXES = ["op."];
const SIS_EXTRA_MODELS = ["hr.employee", "res.company"];

patch(FormStatusIndicator.prototype, {
    get isSisModel() {
        const resModel = this.props.model.root.resModel || "";
        return (
            SIS_MODEL_PREFIXES.some((prefix) => resModel.startsWith(prefix)) ||
            SIS_EXTRA_MODELS.includes(resModel)
        );
    },

    // Toujours afficher les boutons sur les pages EduTek.
    get displayButtons() {
        if (this.isSisModel) return true;
        return this.indicatorMode !== "saved";
    },
});
