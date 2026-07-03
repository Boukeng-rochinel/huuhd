/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";

export class SisDashboard extends Component {
    static template = "edutek_management_cm.SisDashboard";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            loading: true,
            data: null,
            now: new Date(),
        });

        onWillStart(async () => {
            this.state.data = await this.orm.call("res.company", "get_sis_dashboard_data", []);
            this.state.loading = false;
        });

        let timer;
        onMounted(() => {
            timer = setInterval(() => {
                this.state.now = new Date();
            }, 1000);
        });
        onWillUnmount(() => clearInterval(timer));
    }

    get clockTime() {
        return this.state.now.toLocaleTimeString("fr-FR");
    }

    get clockDayName() {
        const label = this.state.now.toLocaleDateString("fr-FR", { weekday: "long" });
        return label.charAt(0).toUpperCase() + label.slice(1);
    }

    get clockDay() {
        return this.state.now.getDate();
    }

    get clockMonthYear() {
        const label = this.state.now.toLocaleDateString("fr-FR", { month: "long", year: "numeric" });
        return label.charAt(0).toUpperCase() + label.slice(1);
    }

    get nouveauxPct() {
        const d = this.state.data;
        const total = d.nouveaux + d.anciens;
        return total ? Math.round((d.nouveaux / total) * 100) : 0;
    }

    get anciensPct() {
        return 100 - this.nouveauxPct;
    }

    get pieStyle() {
        const pct = this.nouveauxPct;
        return `background:conic-gradient(#c0392b 0 ${pct}%, #2e7d32 ${pct}% 100%)`;
    }
}

registry.category("actions").add("edutek_management_cm.dashboard", SisDashboard);
