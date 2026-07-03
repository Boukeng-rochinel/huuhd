/** @odoo-module */

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { router } from "@web/core/browser/router";


export class AcademicYearSwitcher extends Component {
    static template = "edutek_primaire_cm.AcademicYearSwitcher";
    static components = { Dropdown, DropdownItem };

    setup() {
        this.orm = useService("orm");
        this.state = useState({ years: [], currentId: false, currentName: "" });
        onWillStart(() => this._load());
    }

    async _load() {
        const data = await this.orm.call("res.users", "get_academic_year_switcher_data", []);
        this.state.years = data.years;
        this.state.currentId = data.current_id;
        this.state.currentName = data.current_name || "Annee academique";
    }

    async selectYear(yearId) {
        if (yearId === this.state.currentId) return;
        await this.orm.call("res.users", "set_current_academic_year", [yearId]);
        router.pushState({}, { reload: true });
    }
}

registry.category("systray").add("AcademicYearSwitcher", {
    Component: AcademicYearSwitcher,
}, { sequence: 14 });
