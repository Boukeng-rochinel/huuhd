/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";
import { Component, useState, onWillStart } from "@odoo/owl";

export class DocTemplates extends Component {
    static template = "edutek_management_cm.DocTemplates";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            types: [],
            templates: [],
            selectedTypeId: null,
            previewLang: null,
        });

        onWillStart(async () => {
            await this.loadBootstrap();
            this.state.loading = false;
        });
    }

    async loadBootstrap() {
        const data = await this.orm.call("op.document.type", "get_doc_template_bootstrap", []);
        this.state.types = data.types;
        this.state.templates = data.templates;
        if (!this.state.types.some((t) => t.id === this.state.selectedTypeId)) {
            this.state.selectedTypeId = this.state.types.length ? this.state.types[0].id : null;
        }
    }

    get selectedType() {
        return this.state.types.find((t) => t.id === this.state.selectedTypeId) || null;
    }

    get templatesForSelectedType() {
        if (!this.selectedType) {
            return [];
        }
        return this.state.templates.filter(
            (tmpl) => tmpl.op_document_type_id && tmpl.op_document_type_id[0] === this.selectedType.id);
    }

    selectType(id) {
        this.state.selectedTypeId = id;
        this.state.previewLang = null;
    }

    showPreview(lang) {
        this.state.previewLang = this.state.previewLang === lang ? null : lang;
    }

    async createTemplate() {
        const docType = this.selectedType;
        if (!docType) {
            return;
        }
        if (docType.channel === "sms") {
            const vals = {
                name: `Modele - ${docType.name}`,
                model_id: docType.model_id[0],
                op_document_type_id: docType.id,
                body: docType.name,
            };
            const [newId] = await this.orm.create("sms.template", [vals]);
            await this.loadBootstrap();
            this.openTemplateForm(newId, true);
            return;
        }
        const vals = {
            name: `Modele - ${docType.name}`,
            subject: docType.name,
            model_id: docType.model_id[0],
            op_document_type_id: docType.id,
        };
        const [newId] = await this.orm.create("mail.template", [vals]);
        await this.loadBootstrap();
        this.openTemplateForm(newId, false);
    }

    openTemplateForm(id, isSms) {
        this.action.doAction(
            {
                type: "ir.actions.act_window",
                res_model: isSms ? "sms.template" : "mail.template",
                res_id: id,
                views: [[false, "form"]],
                target: "new",
            },
            { onClose: () => this.loadBootstrap() }
        );
    }

    async duplicateTemplate(tmpl) {
        await this.orm.call(tmpl.is_sms ? "sms.template" : "mail.template", "copy", [tmpl.id]);
        await this.loadBootstrap();
    }

    deleteTemplate(tmpl) {
        this.dialog.add(ConfirmationDialog, {
            title: "Supprimer le modele",
            body: `Voulez-vous vraiment supprimer "${tmpl.name}" ?`,
            confirmLabel: "Supprimer",
            confirm: async () => {
                await this.orm.unlink(tmpl.is_sms ? "sms.template" : "mail.template", [tmpl.id]);
                await this.loadBootstrap();
            },
            cancel: () => {},
        });
    }

    useTemplate(tmpl) {
        const docType = this.selectedType;
        if (!docType || !docType.model_name) {
            this.notification.add("Modele cible introuvable pour ce type de document.", { type: "warning" });
            return;
        }
        this.dialog.add(SelectCreateDialog, {
            resModel: docType.model_name,
            title: `Choisir un enregistrement (${docType.name})`,
            noCreate: true,
            multiSelect: false,
            onSelected: (resIds) => {
                if (tmpl.is_sms) {
                    this.action.doAction("sms.sms_composer_action_form", {
                        additionalContext: {
                            default_composition_mode: "comment",
                            default_template_id: tmpl.id,
                            default_res_model: docType.model_name,
                            default_res_id: resIds[0],
                        },
                    });
                } else {
                    this.action.doAction("mail.action_email_compose_message_wizard", {
                        additionalContext: {
                            default_composition_mode: "comment",
                            default_template_id: tmpl.id,
                            default_model: docType.model_name,
                            default_res_ids: JSON.stringify(resIds),
                        },
                    });
                }
            },
        });
    }
}

registry.category("actions").add("edutek_management_cm.doc_templates", DocTemplates);
