/** @odoo-module **/

import { renderToElement as coreRenderToElement } from "@web/core/utils/render";

// Monkey patch the function to skip missing template gracefully
export function renderToElement(templateName, ctx) {
    if (templateName === "Appointment.appointment_info_upcoming_appointment") {
        console.warn(`[Skipped rendering]: ${templateName}`);
        const el = document.createElement('div');
        el.classList.add('o_skipped_upcoming_appointment');
        return el;
    }
    return coreRenderToElement(templateName, ctx);
}
