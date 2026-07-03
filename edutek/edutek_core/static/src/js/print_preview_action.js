/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, useState, useRef, onWillStart, onWillUnmount } from "@odoo/owl";

export class PrintPreviewDialog extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.iframeRef = useRef("iframe");

        this.title = this.props.title || "Apercu du document";
        this.rpcKwargs = this.props.reportContext ? { context: this.props.reportContext } : {};

        this.state = useState({ loading: true, pdfUrl: null, downloading: false });

        onWillStart(() => this.loadPreview());
        onWillUnmount(() => {
            if (this.state.pdfUrl) {
                URL.revokeObjectURL(this.state.pdfUrl);
            }
        });
    }

    async loadPreview() {
        const base64Pdf = await this.orm.call(
            "ir.actions.report", "render_pdf_base64",
            [this.props.reportXmlId, this.props.resModel, this.props.resIds, this.props.reportData],
            this.rpcKwargs);
        const raw = atob(base64Pdf);
        const bytes = new Uint8Array(raw.length);
        for (let i = 0; i < raw.length; i++) {
            bytes[i] = raw.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: "application/pdf" });
        this.state.pdfUrl = URL.createObjectURL(blob);
        this.state.loading = false;
    }

    printDocument() {
        const iframe = this.iframeRef.el;
        if (iframe && iframe.contentWindow) {
            iframe.contentWindow.focus();
            iframe.contentWindow.print();
        }
    }

    async downloadPdf() {
        this.state.downloading = true;
        try {
            const downloadAction = await this.orm.call(
                "ir.actions.report", "get_generic_report_action",
                [this.props.reportXmlId, this.props.resModel, this.props.resIds, this.props.reportData],
                this.rpcKwargs);
            await this.action.doAction(downloadAction);
        } finally {
            this.state.downloading = false;
        }
    }

    close() {
        this.props.close();
    }
}

PrintPreviewDialog.template = "edutek_core.print_preview_action";
PrintPreviewDialog.components = { Dialog };
PrintPreviewDialog.props = {
    close: Function,
    title: { type: String, optional: true },
    reportXmlId: String,
    resModel: String,
    resIds: Array,
    reportData: { optional: true },
    reportContext: { optional: true },
};

function openPrintPreview(env, action) {
    const params = action.params || {};
    env.services.dialog.add(PrintPreviewDialog, {
        title: params.title,
        reportXmlId: params.report_xmlid,
        resModel: params.res_model,
        resIds: params.res_ids || [],
        reportData: params.data || false,
        reportContext: params.context || false,
    });
}

registry.category("actions").add("edutek_core.print_preview", openPrintPreview);
