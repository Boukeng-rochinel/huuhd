/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

const STATE_LABELS = {
    installed: "Installe",
    uninstalled: "Non installe",
    uninstallable: "Non installable",
    "to install": "A installer",
    "to upgrade": "A mettre a jour",
    "to remove": "A desinstaller",
};

const STATE_CLASSES = {
    installed: "emi-state--ok",
    "to install": "emi-state--warn",
    "to upgrade": "emi-state--warn",
    "to remove": "emi-state--warn",
};

const FIELDS = [
    "name", "shortdesc", "summary", "author",
    "installed_version", "state", "icon_image",
];

export class EdutekModulesInfo extends Component {
    static template = "edutek_management_cm.EdutekModulesInfo";

    setup() {
        this.orm = useService("orm");
        this.state = useState({ loading: true, modules: [] });

        onWillStart(async () => {
            this.state.modules = await this.orm.searchRead(
                "ir.module.module", [["name", "like", "edutek"]], FIELDS, { order: "name" });
            this.state.loading = false;
        });
    }

    stateLabel(state) {
        return STATE_LABELS[state] || state;
    }

    stateClass(state) {
        return STATE_CLASSES[state] || "emi-state--off";
    }

    iconSrc(mod) {
        return "data:image/png;base64," + mod.icon_image;
    }
}

registry.category("actions").add("edutek_management_cm.edutek_modules_info", EdutekModulesInfo);
