/** @odoo-module */

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { sisLockState } from "./lock_state";


export class SisLockButton extends Component {
    static template = "edutek_management_cm.SisLockButton";

    lock() {
        sisLockState.locked = true;
        sisLockState.unlockedOnce = false;
    }
}

registry.category("systray").add("sis_lock_button", {
    Component: SisLockButton,
}, { sequence: 15 });
