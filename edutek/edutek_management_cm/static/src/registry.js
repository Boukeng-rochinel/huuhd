/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

const PAGE_SIZE = 50;

const DEFAULT_FILTERS = {
    search: "",
    inscriptionState: "tous",
    enrollmentType: "tous",
    classeId: false,
    enfantEnseignant: false,
    deficientIntellectuel: false,
    dateFrom: false,
    dateTo: false,
};

export class StudentRegistry extends Component {
    static template = "edutek_management_cm.StudentRegistry";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            loading: true,
            students: [],
            documentTypes: [],
            documentsByStudent: {},
            classes: [],
            total: 0,
            page: 0,
            filters: { ...DEFAULT_FILTERS },
            actionsOpen: false,
            effectif: null,
            periodeDialog: false,
            periodeFrom: "",
            periodeTo: "",
        });

        onWillStart(async () => {
            this.state.classes = await this.orm.searchRead("op.classe", [], ["display_name"], { order: "name" });
            await this.loadPage();
            this.state.loading = false;
        });
    }

    get totalPages() {
        return Math.max(1, Math.ceil(this.state.total / PAGE_SIZE));
    }

    get backendFilters() {
        const f = this.state.filters;
        return {
            search: f.search || false,
            inscription_state: f.inscriptionState,
            enrollment_type: f.enrollmentType,
            classe_id: f.classeId || false,
            enfant_enseignant: f.enfantEnseignant || false,
            deficient_intellectuel: f.deficientIntellectuel || false,
            date_from: f.dateFrom || false,
            date_to: f.dateTo || false,
        };
    }

    get hasExtraFilter() {
        return this.state.filters.enfantEnseignant || this.state.filters.deficientIntellectuel
            || this.state.filters.dateFrom || this.state.filters.dateTo;
    }

    async loadPage() {
        const data = await this.orm.call("op.student", "get_registry_page", [
            this.backendFilters, PAGE_SIZE, this.state.page * PAGE_SIZE,
        ]);
        this.state.total = data.total;
        this.state.students = data.students;
        this.state.documentTypes = data.document_types;

        const byStudent = {};
        for (const doc of data.documents) {
            const sid = doc.student_id[0];
            const tid = doc.document_type_id[0];
            byStudent[sid] = byStudent[sid] || {};
            byStudent[sid][tid] = doc.provided;
        }
        this.state.documentsByStudent = byStudent;
    }

    async reload() {
        this.state.page = 0;
        await this.loadPage();
    }

    onSearchInput(ev) {
        this.state.filters.search = ev.target.value;
        this.reload();
    }

    setInscriptionState(value) {
        this.state.filters.inscriptionState = value;
        this.reload();
    }

    setEnrollmentType(value) {
        this.state.filters.enrollmentType = value;
        this.reload();
    }

    onClasseChange(ev) {
        this.state.filters.classeId = ev.target.value ? Number(ev.target.value) : false;
        this.reload();
    }

    async prevPage() {
        if (this.state.page > 0) {
            this.state.page -= 1;
            await this.loadPage();
        }
    }

    async nextPage() {
        if (this.state.page < this.totalPages - 1) {
            this.state.page += 1;
            await this.loadPage();
        }
    }

    isDocProvided(studentId, docTypeId) {
        return !!(this.state.documentsByStudent[studentId] && this.state.documentsByStudent[studentId][docTypeId]);
    }

    async toggleDocument(studentId, docTypeId) {
        const current = this.isDocProvided(studentId, docTypeId);
        this.state.documentsByStudent[studentId] = this.state.documentsByStudent[studentId] || {};
        this.state.documentsByStudent[studentId][docTypeId] = !current;
        await this.orm.call("op.student.document", "set_provided", [studentId, docTypeId, !current]);
    }

    toggleActions() {
        this.state.actionsOpen = !this.state.actionsOpen;
    }

    closeActions() {
        this.state.actionsOpen = false;
    }

    async actionEffectif() {
        this.closeActions();
        this.state.effectif = await this.orm.call("op.student", "get_effectif_par_classe", [this.backendFilters]);
    }

    closeEffectif() {
        this.state.effectif = null;
    }

    actionEnfantEnseignant() {
        this.closeActions();
        this.state.filters.enfantEnseignant = true;
        this.reload();
    }

    actionDeficientIntellectuel() {
        this.closeActions();
        this.state.filters.deficientIntellectuel = true;
        this.reload();
    }

    clearExtraFilters() {
        this.state.filters.enfantEnseignant = false;
        this.state.filters.deficientIntellectuel = false;
        this.state.filters.dateFrom = false;
        this.state.filters.dateTo = false;
        this.reload();
    }

    actionAncienNouveau() {
        this.closeActions();
        const context = {
            default_inscription_state: this.state.filters.inscriptionState !== "tous"
                ? this.state.filters.inscriptionState : "inscrit",
            default_enrollment_type: this.state.filters.enrollmentType,
        };
        if (this.state.filters.classeId) {
            context.default_classe_ids = [this.state.filters.classeId];
        }
        this.action.doAction("edutek_primaire_cm.action_op_student_list_wizard", {
            additionalContext: context,
        });
    }

    actionExporter() {
        this.closeActions();
        const context = {
            default_inscription_state: this.state.filters.inscriptionState,
            default_enrollment_type: this.state.filters.enrollmentType,
        };
        if (this.state.filters.classeId) {
            context.default_classe_ids = [this.state.filters.classeId];
        }
        if (this.state.filters.dateFrom) {
            context.default_date_from = this.state.filters.dateFrom;
        }
        if (this.state.filters.dateTo) {
            context.default_date_to = this.state.filters.dateTo;
        }
        this.action.doAction("edutek_primaire_cm.action_op_student_list_wizard", {
            additionalContext: context,
        });
    }

    actionPeriode() {
        this.closeActions();
        this.state.periodeDialog = true;
    }

    closePeriodeDialog() {
        this.state.periodeDialog = false;
    }

    applyPeriode() {
        this.state.periodeDialog = false;
        this.state.filters.dateFrom = this.state.periodeFrom || false;
        this.state.filters.dateTo = this.state.periodeTo || false;
        this.reload();
    }
}

registry.category("actions").add("edutek_management_cm.student_registry", StudentRegistry);
