/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { DocTemplates } from "./doc_templates";
import { Component, useState, onWillStart } from "@odoo/owl";
import { sisLockState } from "./lock_state";

const EMPTY_DRAFT = {
    name: "",
    level: false,
    serie: false,
    deuxieme_langue: false,
    intitule_abrege: "",
    matricule_prefix: "",
    teacher_id: false,
    moy_min_passage_trimestre: 10,
    moy_min_passage_annee: 10,
    bulletin_double: false,
    bulletin_multi_pages: false,
    determinant_reussite: "annuel",
    type_bulletin: "defaut",
};

const NIVEAUX_ROW_MODELS = {
    cycle: "op.education.cycle",
    section: "op.education.section",
    level: "op.education.level",
    serie: "op.education.serie",
};

const JOURNAL_TYPE_LABELS = {
    sale: "Vente",
    purchase: "Achat",
    cash: "Caisse",
    bank: "Banque",
    general: "Divers",
    credit: "Carte de credit",
};

export class ClasseConfig extends Component {
    static template = "edutek_management_cm.ClasseConfig";
    static components = { DocTemplates };

    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.action = useService("action");

        this.state = useState({
            loading: true,
            activeTab: "structures",
            classes: [],
            selections: {},
            currentYearId: false,
            selectedId: null,
            editMode: false,
            isNew: false,
            saving: false,
            draft: null,
            feeLines: [],
            feeTypes: [],
            newFeeLine: { fee_type_id: false, amount: 0 },

            infoLoaded: false,
            schoolInfoDraft: null,
            savingInfo: false,

            matriculeLoaded: false,
            matriculeDraft: null,
            savingMatricule: false,

            employees: [],

            journalsLoaded: false,
            journals: [],

            personnelLoaded: false,
            staffTypes: [],
            grades: [],
            newStaffTypeName: "",
            newGradeName: "",

            niveauxLoaded: false,
            cycles: [],
            sections: [],
            levels: [],
            series: [],
            newCycleName: "",
            newSectionName: "",
            newSerieName: "",
            newLevel: { name: "", code: "", cycle_id: false, section_id: false },
            editingRow: null,
        });

        onWillStart(async () => {
            await this.loadBootstrap();
            this.state.loading = false;
        });
    }

    async switchTab(tab) {
        this.state.activeTab = tab;
        if (tab === "info" && !this.state.infoLoaded) {
            await this.loadSchoolInfo();
        } else if (tab === "matricule" && !this.state.matriculeLoaded) {
            await this.loadMatricule();
        } else if (tab === "journaux" && !this.state.journalsLoaded) {
            await this.loadJournals();
        } else if (tab === "personnel" && !this.state.personnelLoaded) {
            await this.loadPersonnel();
        } else if (tab === "niveaux" && !this.state.niveauxLoaded) {
            await this.loadNiveaux();
        }
    }

    journalTypeLabel(type) {
        return JOURNAL_TYPE_LABELS[type] || type;
    }

    // ------------------------------------------------------------------
    // Onglet "Informations" (fiche d'identite de l'ecole)
    // ------------------------------------------------------------------
    async loadSchoolInfo() {
        const info = await this.orm.call("res.company", "get_school_info", []);
        this.state.schoolInfoDraft = { ...info };
        this.state.infoLoaded = true;
    }

    onLogoChange(ev) {
        const file = ev.target.files[0];
        if (!file) {
            return;
        }
        const reader = new FileReader();
        reader.onload = () => {
            this.state.schoolInfoDraft.logo = reader.result.split(",")[1];
        };
        reader.readAsDataURL(file);
    }

    onCertificateBackgroundChange(ev) {
        const file = ev.target.files[0];
        if (!file) {
            return;
        }
        const reader = new FileReader();
        reader.onload = () => {
            this.state.schoolInfoDraft.certificate_background = reader.result.split(",")[1];
            this.state.schoolInfoDraft.certificate_background_filename = file.name;
        };
        reader.readAsDataURL(file);
    }

    removeCertificateBackground() {
        this.state.schoolInfoDraft.certificate_background = false;
        this.state.schoolInfoDraft.certificate_background_filename = false;
    }

    async saveSchoolInfo() {
        this.state.savingInfo = true;
        try {
            await this.orm.call("res.company", "set_school_info", [this.state.schoolInfoDraft]);
            this.notification.add("Informations de l'ecole enregistrees.", { type: "success" });
        } finally {
            this.state.savingInfo = false;
        }
    }

    // ------------------------------------------------------------------
    // Onglet "Matricule" (numerotation des eleves)
    // ------------------------------------------------------------------
    async loadMatricule() {
        const config = await this.orm.call("res.company", "get_matricule_config", []);
        this.state.matriculeDraft = { ...config };
        this.state.matriculeLoaded = true;
    }

    async saveMatricule() {
        this.state.savingMatricule = true;
        try {
            await this.orm.call("res.company", "set_matricule_config", [this.state.matriculeDraft]);
            await this.loadMatricule();
            this.notification.add("Configuration du matricule enregistree.", { type: "success" });
        } finally {
            this.state.savingMatricule = false;
        }
    }

    // ------------------------------------------------------------------
    // Onglet "Journaux" (caisses/journaux utilises par l'ecole)
    // ------------------------------------------------------------------
    async loadJournals() {
        this.state.journals = await this.orm.searchRead(
            "account.journal", [], ["name", "code", "type", "school_active"],
            { order: "type, name" });
        this.state.journalsLoaded = true;
    }

    async toggleJournalActive(journal) {
        const value = !journal.school_active;
        await this.orm.write("account.journal", [journal.id], { school_active: value });
        journal.school_active = value;
    }

    openJournalForm(journalId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "account.journal",
            views: [[false, "form"]],
            res_id: journalId || false,
            target: "new",
        }, {
            onClose: () => this.loadJournals(),
        });
    }

    // ------------------------------------------------------------------
    // Onglet "Personnel" (types de personnel / grades editables)
    // ------------------------------------------------------------------
    async loadPersonnel() {
        const [staffTypes, grades] = await Promise.all([
            this.orm.searchRead("op.staff.type", [], ["name", "code"], { order: "sequence, name" }),
            this.orm.searchRead("op.grade", [], ["name"], { order: "sequence, name" }),
        ]);
        this.state.staffTypes = staffTypes;
        this.state.grades = grades;
        this.state.personnelLoaded = true;
    }

    async addStaffType() {
        if (!this.state.newStaffTypeName.trim()) {
            return;
        }
        await this.orm.create("op.staff.type", [{ name: this.state.newStaffTypeName.trim() }]);
        this.state.newStaffTypeName = "";
        await this.loadPersonnel();
    }

    async removeStaffType(staffType) {
        await this.orm.unlink("op.staff.type", [staffType.id]);
        await this.loadPersonnel();
    }

    async addGrade() {
        if (!this.state.newGradeName.trim()) {
            return;
        }
        await this.orm.create("op.grade", [{ name: this.state.newGradeName.trim() }]);
        this.state.newGradeName = "";
        await this.loadPersonnel();
    }

    async removeGrade(grade) {
        await this.orm.unlink("op.grade", [grade.id]);
        await this.loadPersonnel();
    }

    // ------------------------------------------------------------------
    // Onglet "Niveaux & Cycles" (structure pedagogique editable :
    // cycles, sections, niveaux, series)
    // ------------------------------------------------------------------
    async loadNiveaux() {
        const [cycles, sections, levels, series] = await Promise.all([
            this.orm.searchRead("op.education.cycle", [], ["name", "code"], { order: "sequence, name" }),
            this.orm.searchRead("op.education.section", [], ["name", "code"], { order: "sequence, name" }),
            this.orm.searchRead(
                "op.education.level", [], ["name", "code", "cycle_id", "section_id"],
                { order: "sequence, name" }),
            this.orm.searchRead("op.education.serie", [], ["name", "code"], { order: "sequence, name" }),
        ]);
        this.state.cycles = cycles;
        this.state.sections = sections;
        this.state.levels = levels;
        this.state.series = series;
        this.state.niveauxLoaded = true;
    }

    async addCycle() {
        if (!this.state.newCycleName.trim()) {
            return;
        }
        const name = this.state.newCycleName.trim();
        await this.orm.create("op.education.cycle", [{ name, code: name.toLowerCase() }]);
        this.state.newCycleName = "";
        await this.loadNiveaux();
    }

    async removeCycle(cycle) {
        await this.orm.unlink("op.education.cycle", [cycle.id]);
        await this.loadNiveaux();
    }

    async addSection() {
        if (!this.state.newSectionName.trim()) {
            return;
        }
        const name = this.state.newSectionName.trim();
        await this.orm.create("op.education.section", [{ name, code: name.toLowerCase() }]);
        this.state.newSectionName = "";
        await this.loadNiveaux();
    }

    async removeSection(section) {
        await this.orm.unlink("op.education.section", [section.id]);
        await this.loadNiveaux();
    }

    async addSerie() {
        if (!this.state.newSerieName.trim()) {
            return;
        }
        const name = this.state.newSerieName.trim();
        await this.orm.create("op.education.serie", [{ name, code: name.toLowerCase() }]);
        this.state.newSerieName = "";
        await this.loadNiveaux();
    }

    async removeSerie(serie) {
        await this.orm.unlink("op.education.serie", [serie.id]);
        await this.loadNiveaux();
    }

    async addLevel() {
        const { name, code, cycle_id, section_id } = this.state.newLevel;
        if (!name.trim() || !code.trim() || !cycle_id) {
            this.notification.add(
                "Nom, code et cycle sont obligatoires pour un niveau.", { type: "warning" });
            return;
        }
        await this.orm.create("op.education.level", [{
            name: name.trim(),
            code: code.trim(),
            cycle_id,
            section_id: section_id || false,
        }]);
        this.state.newLevel = { name: "", code: "", cycle_id: false, section_id: false };
        await this.loadNiveaux();
    }

    async removeLevel(level) {
        await this.orm.unlink("op.education.level", [level.id]);
        await this.loadNiveaux();
    }

    // ------------------------------------------------------------------
    // Edition en ligne (clic sur une ligne existante de cycle/section/
    // niveau/serie) : un seul etat d'edition partage par les 4 tableaux,
    // discrimine par `kind` (clef de NIVEAUX_ROW_MODELS).
    // ------------------------------------------------------------------
    startEditRow(kind, item) {
        const draft = { name: item.name, code: item.code };
        if (kind === "level") {
            draft.cycle_id = item.cycle_id ? item.cycle_id[0] : false;
            draft.section_id = item.section_id ? item.section_id[0] : false;
        }
        this.state.editingRow = { kind, id: item.id, draft };
    }

    isEditingRow(kind, id) {
        return !!(this.state.editingRow
            && this.state.editingRow.kind === kind
            && this.state.editingRow.id === id);
    }

    cancelEditRow() {
        this.state.editingRow = null;
    }

    onEditRowKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.saveEditRow();
        } else if (ev.key === "Escape") {
            ev.preventDefault();
            this.cancelEditRow();
        }
    }

    async saveEditRow() {
        const editing = this.state.editingRow;
        if (!editing) {
            return;
        }
        const draft = { ...editing.draft };
        if (!draft.name || !draft.name.trim() || !draft.code || !draft.code.trim()) {
            this.notification.add(
                "Le nom et le code sont obligatoires.", { type: "warning" });
            return;
        }
        await this.orm.write(NIVEAUX_ROW_MODELS[editing.kind], [editing.id], draft);
        this.state.editingRow = null;
        await this.loadNiveaux();
    }

    async loadBootstrap() {
        const data = await this.orm.call("op.classe", "get_classe_config_bootstrap", []);
        this.state.selections = data.selections;
        this.state.currentYearId = data.current_year_id;
        this.state.classes = data.classes;
        this.state.feeLines = data.fee_lines;
        this.state.feeTypes = data.fee_types;
        this.state.employees = data.employees || [];
        if (!this.state.classes.some((c) => c.id === this.state.selectedId)) {
            this.state.selectedId = this.state.classes.length ? this.state.classes[0].id : null;
        }
    }

    get visibleClasses() {
        const emp = sisLockState.activeEmployee;
        if (!emp || emp.role !== "teacher") {
            return this.state.classes;
        }
        return this.state.classes.filter((c) => {
            const tid = Array.isArray(c.teacher_id) ? c.teacher_id[0] : c.teacher_id;
            return tid === emp.id;
        });
    }

    get selected() {
        return this.state.classes.find((c) => c.id === this.state.selectedId) || null;
    }

    teacherName(teacherId) {
        if (!teacherId) return "-";
        const id = Array.isArray(teacherId) ? teacherId[0] : teacherId;
        const name = Array.isArray(teacherId) ? teacherId[1] : null;
        if (name) return name;
        const emp = this.state.employees.find((e) => e.id === id);
        return emp ? emp.name : "-";
    }

    onTeacherChange(ev) {
        this.state.draft.teacher_id = ev.target.value ? Number(ev.target.value) : false;
    }

    get feeLinesForSelected() {
        if (!this.selected) {
            return [];
        }
        return this.state.feeLines.filter(
            (line) => line.classe_id && line.classe_id[0] === this.selected.id);
    }

    async addFeeLine() {
        if (!this.selected || !this.state.newFeeLine.fee_type_id) {
            return;
        }
        await this.orm.create("op.classe.fee", [{
            classe_id: this.selected.id,
            fee_type_id: this.state.newFeeLine.fee_type_id,
            amount: this.state.newFeeLine.amount || 0,
        }]);
        this.state.newFeeLine = { fee_type_id: false, amount: 0 };
        await this.loadBootstrap();
    }

    async updateFeeLineAmount(line, amount) {
        await this.orm.write("op.classe.fee", [line.id], { amount: Number(amount) || 0 });
        line.amount = Number(amount) || 0;
    }

    async removeFeeLine(line) {
        await this.orm.unlink("op.classe.fee", [line.id]);
        await this.loadBootstrap();
    }

    selectionLabel(fieldName, value) {
        if (!value) {
            return "-";
        }
        const pairs = this.state.selections[fieldName] || [];
        const found = pairs.find((p) => p[0] === value);
        return found ? found[1] : value;
    }

    classeFeesTotal(classeId) {
        return this.state.feeLines
            .filter((line) => line.classe_id && line.classe_id[0] === classeId)
            .reduce((sum, line) => sum + line.amount, 0);
    }

    formatAmount(amount) {
        return new Intl.NumberFormat("fr-FR", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(amount || 0);
    }

    selectClasse(id) {
        this.state.selectedId = id;
        this.state.editMode = false;
        this.state.isNew = false;
        this.state.draft = null;
    }

    startEdit() {
        if (!this.selected) {
            return;
        }
        const draft = { ...this.selected };
        draft.teacher_id = Array.isArray(draft.teacher_id) ? draft.teacher_id[0] : (draft.teacher_id || false);
        this.state.draft = draft;
        this.state.isNew = false;
        this.state.editMode = true;
    }

    startCreate() {
        this.state.selectedId = null;
        this.state.isNew = true;
        this.state.editMode = true;
        this.state.draft = { ...EMPTY_DRAFT };
    }

    cancelEdit() {
        this.state.editMode = false;
        this.state.isNew = false;
        this.state.draft = null;
        if (!this.selected && this.state.classes.length) {
            this.state.selectedId = this.state.classes[0].id;
        }
    }

    async save() {
        if (!this.state.draft.name || !this.state.draft.level) {
            this.notification.add("Le nom et le niveau sont obligatoires.", { type: "warning" });
            return;
        }
        this.state.saving = true;
        try {
            const vals = { ...this.state.draft };
            delete vals.id;
            delete vals.student_count;
            if (this.state.isNew) {
                vals.academic_year_id = this.state.currentYearId;
                const [newId] = await this.orm.create("op.classe", [vals]);
                await this.loadBootstrap();
                this.state.selectedId = newId;
            } else {
                await this.orm.write("op.classe", [this.state.draft.id], vals);
                const id = this.state.draft.id;
                await this.loadBootstrap();
                this.state.selectedId = id;
            }
            this.state.editMode = false;
            this.state.isNew = false;
            this.state.draft = null;
        } finally {
            this.state.saving = false;
        }
    }

    deleteSelected() {
        if (!this.selected) {
            return;
        }
        const classe = this.selected;
        this.dialog.add(ConfirmationDialog, {
            title: "Supprimer la classe",
            body: `Voulez-vous vraiment supprimer "${classe.name}" ?`,
            confirmLabel: "Supprimer",
            confirm: async () => {
                await this.orm.unlink("op.classe", [classe.id]);
                this.state.selectedId = null;
                await this.loadBootstrap();
            },
            cancel: () => {},
        });
    }
}

registry.category("actions").add("edutek_management_cm.classe_config", ClasseConfig);
