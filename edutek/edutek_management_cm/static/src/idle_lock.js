/** @odoo-module */

import { sisLockState } from "./lock_state";

// Duree d'inactivite avant verrouillage automatique (en ms).
const IDLE_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

let idleTimer = null;
let lastReset = 0;

function arm(force) {
    if (sisLockState.locked && !force) return;
    const now = Date.now();
    if (!force && now - lastReset < 1000) return; // throttle
    lastReset = now;
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        sisLockState.locked = true;
        sisLockState.unlockedOnce = false; // re-authentification requise au retour
    }, IDLE_TIMEOUT_MS);
}

// A appeler explicitement apres un deverrouillage pour redemarrer le compteur
// meme si l'utilisateur ne bouge pas immediatement la souris.
export function armIdleTimer() {
    arm(true);
}

["mousemove", "mousedown", "keydown", "scroll", "touchstart", "click"].forEach((evt) => {
    document.addEventListener(evt, () => arm(false), { passive: true, capture: true });
});

arm(true);
