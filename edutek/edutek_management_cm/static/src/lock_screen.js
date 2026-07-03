/** @odoo-module */

import { Component, useState, useEffect, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService, useBus } from "@web/core/utils/hooks";
import { sisLockState } from "./lock_state";
import { armIdleTimer } from "./idle_lock";

const AVATAR_COLORS = [
    "#7C3AED", "#DB2777", "#EA580C", "#0D9488",
    "#16A34A", "#CA8A04", "#DC2626", "#9333EA",
    "#0891B2", "#4F46E5",
];

export class SisLockScreen extends Component {
    static template = "edutek_management_cm.SisLockScreen";

    setup() {
        this.lockState = useState(sisLockState);
        this.state = useState({
            phase: "select",           // "select" | "pin"
            employees: [],
            loadingEmployees: false,
            selected: null,            // { id, name }
            pin: "",
            error: false,
            loading: false,
        });
        this.orm = useService("orm");
        this.menu = useService("menu");
        this.sisMenuId = null;

        useEffect(
            () => {
                if (this.lockState.locked) {
                    sisLockState.activeEmployee = null;
                    this._reset();
                    this._loadEmployees();
                }
            },
            () => [this.lockState.locked]
        );

        // Detecte l'entree dans l'application EduTek pour en faire la
        // porte d'authentification, comme le selecteur de caissier du POS.
        this._initSisGate();
        useBus(this.env.bus, "MENUS:APP-CHANGED", () => this._checkSisGate());
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => this._checkSisGate());
        onMounted(() => this._checkSisGate());

        this._onKeyDown = this._onKeyDown.bind(this);
        onMounted(() => document.addEventListener("keydown", this._onKeyDown));
        onWillUnmount(() => document.removeEventListener("keydown", this._onKeyDown));
    }

    // Permet de saisir le code PIN directement au clavier physique,
    // en plus du pave numerique tactile.
    _onKeyDown(ev) {
        if (!this.lockState.locked || this.state.phase !== "pin") {
            return;
        }
        if (ev.key >= "0" && ev.key <= "9") {
            ev.preventDefault();
            this.pressDigit(Number(ev.key));
        } else if (ev.key === "Backspace") {
            ev.preventDefault();
            this.backspace();
        } else if (ev.key === "Enter") {
            ev.preventDefault();
            this.validate();
        } else if (ev.key === "Escape") {
            ev.preventDefault();
            this.backToSelect();
        }
    }

    async _initSisGate() {
        try {
            this.sisMenuId = await this.orm.call("hr.employee", "get_sis_root_menu_id", []);
        } catch (_) {
            this.sisMenuId = null;
        }
        this._checkSisGate();
    }

    _checkSisGate() {
        if (!this.sisMenuId) return;
        const app = this.menu.getCurrentApp();
        if (app && app.id === this.sisMenuId && !sisLockState.unlockedOnce) {
            sisLockState.locked = true;
        }
    }

    _reset() {
        this.state.phase = "select";
        this.state.selected = null;
        this.state.pin = "";
        this.state.error = false;
    }

    async _loadEmployees() {
        this.state.loadingEmployees = true;
        try {
            const employees = await this.orm.call(
                "hr.employee", "get_sis_lock_employees", []
            );
            this.state.employees = employees;
        } catch (_) {
            this.state.employees = [];
        } finally {
            this.state.loadingEmployees = false;
        }
    }

    // ── Phase 1 : selection ───────────────────────────────────────────────

    selectEmployee(emp) {
        this.state.selected = emp;
        this.state.phase = "pin";
        this.state.pin = "";
        this.state.error = false;
    }

    backToSelect() {
        this._reset();
    }

    // ── Phase 2 : saisie PIN ──────────────────────────────────────────────

    pressDigit(digit) {
        if (this.state.loading || this.state.pin.length >= 6) return;
        this.state.pin += String(digit);
        this.state.error = false;
    }

    backspace() {
        if (this.state.loading) return;
        this.state.pin = this.state.pin.slice(0, -1);
        this.state.error = false;
    }

    async validate() {
        if (!this.state.pin || this.state.loading || !this.state.selected) return;
        this.state.loading = true;
        try {
            const result = await this.orm.call(
                "hr.employee",
                "check_employee_sis_pin",
                [this.state.selected.id, this.state.pin]
            );
            if (result) {
                sisLockState.locked = false;
                sisLockState.unlockedOnce = true;
                sisLockState.activeEmployee = {
                    id: result.id || this.state.selected.id,
                    name: result.name || this.state.selected.name,
                    role: result.role || 'admin',
                };
                armIdleTimer();
            } else {
                this.state.error = true;
                this.state.pin = "";
            }
        } catch (_) {
            this.state.error = true;
            this.state.pin = "";
        } finally {
            this.state.loading = false;
        }
    }

    get pinDots() {
        return Array.from({ length: 6 }, (_, i) => i < this.state.pin.length);
    }

    getColor(id) {
        return AVATAR_COLORS[id % AVATAR_COLORS.length];
    }

    getInitial(name) {
        return (name || "?").trim().charAt(0).toUpperCase();
    }
}

registry.category("main_components").add("SisLockScreen", {
    Component: SisLockScreen,
});
