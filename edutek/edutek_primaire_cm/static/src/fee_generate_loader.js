/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

// Tous les modeles EduTek commencent par "op." - on couvre aussi les
// wizards (op.*.wizard) et les modeles metier (op.student, op.classe...).
const EDUTEK_PREFIX = "op.";

// Injecte une seule fois les @keyframes du spinner dans le <head>.
function ensureKeyframes() {
    if (document.getElementById("o_edutek_spin_kf")) return;
    const style = document.createElement("style");
    style.id = "o_edutek_spin_kf";
    style.textContent = "@keyframes o_edutek_spin{to{transform:rotate(360deg)}}";
    document.head.appendChild(style);
}

function buildOverlay() {
    ensureKeyframes();

    const overlay = document.createElement("div");
    overlay.style.cssText = [
        "position:absolute", "inset:0",
        "background:rgba(255,255,255,0.88)",
        "display:flex", "flex-direction:column",
        "align-items:center", "justify-content:center",
        "gap:14px", "z-index:9999",
        "border-radius:inherit",
    ].join(";");

    const ring = document.createElement("div");
    ring.style.cssText = [
        "width:52px", "height:52px",
        "border-radius:50%",
        "border:5px solid #e0d0dc",
        "border-top-color:#714B67",
        "animation:o_edutek_spin 0.75s linear infinite",
    ].join(";");

    const label = document.createElement("p");
    label.textContent = "Veuillez patienter …";
    label.style.cssText = [
        "margin:0", "font-size:15px",
        "font-weight:600", "color:#714B67",
        "letter-spacing:0.2px",
    ].join(";");

    overlay.appendChild(ring);
    overlay.appendChild(label);
    return overlay;
}

patch(FormController.prototype, {
    async onClickButton(button, ev) {
        const resModel = this.model?.root?.resModel;
        if (!resModel?.startsWith(EDUTEK_PREFIX)) {
            return super.onClickButton(button, ev);
        }

        // Cible le panneau de contenu du dialogue pour ne pas couvrir le
        // chrome entier - l'overlay reste confine a l'interieur du modal.
        const dialogPanel =
            this.el?.closest(".o_dialog_content") ||
            this.el?.closest(".o_dialog") ||
            this.el;

        const savedPos = dialogPanel?.style.position;
        if (dialogPanel && !dialogPanel.style.position) {
            dialogPanel.style.position = "relative";
        }

        const overlay = buildOverlay();
        dialogPanel?.appendChild(overlay);

        try {
            return await super.onClickButton(button, ev);
        } finally {
            overlay.remove();
            if (dialogPanel && savedPos !== undefined) {
                dialogPanel.style.position = savedPos;
            }
        }
    },
});
