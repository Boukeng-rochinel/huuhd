/** @odoo-module */

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { router } from "@web/core/browser/router";

export class EduTekLangToggle extends Component {
    static template = "edutek_core.LangToggle";
    static props = {};

    setup() {
        this.orm = useService("orm");
    }

    get isFrench() {
        const lang =
            window.__session_info?.user_context?.lang ||
            window.odoo?.session_info?.user_context?.lang ||
            document.documentElement.lang ||
            "fr_FR";
        return lang.startsWith("fr");
    }

    get title() {
        return this.isFrench ? "Switch to English" : "Basculer en Français";
    }

    async toggle() {
        const newLang = this.isFrench ? "en_US" : "fr_FR";
        const uid =
            window.__session_info?.uid ||
            window.odoo?.session_info?.uid;
        if (uid) {
            await this.orm.write("res.users", [uid], { lang: newLang });
        }
        router.pushState({}, { reload: true });
    }
}

registry.category("systray").add("edutek_lang_toggle", {
    Component: EduTekLangToggle,
}, { sequence: 13 });
