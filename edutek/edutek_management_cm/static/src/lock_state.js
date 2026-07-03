/** @odoo-module */

import { reactive } from "@odoo/owl";

/**
 * Etat global reactif du verrou EduTek.
 * Importe directement par les composants qui ont besoin de lire ou ecrire l'etat.
 *
 * - locked       : l'overlay de verrouillage est affiche.
 * - unlockedOnce : l'utilisateur s'est deja authentifie une fois dans cette
 *                  session navigateur. Empeche de redemander a chaque clic de
 *                  menu dans le EduTek ; remis a false par le minuteur d'inactivite.
 */
export const sisLockState = reactive({ locked: false, unlockedOnce: false, activeEmployee: null });
