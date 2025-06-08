/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { URL } from "@web/core/utils/urls";

publicWidget.registry.appointmentSlotSelectExtended = publicWidget.registry.appointmentSlotSelect.extend({
    /**
     * Extends the _onClickConfirmSlot method to include the slot_id in the submission
     * and log the slot details in the console.
     */
    _onClickConfirmSlot: function (ev) {
        console.log("Confirm Slot Clicked"); // Debugging line to ensure function is triggered

        const appointmentTypeID = this.el.querySelector("input[name='appointment_type_id']")?.value;
        if (!appointmentTypeID) {
            console.error("Appointment Type ID not found");
            return;
        }
        console.log(`Appointment Type ID: ${appointmentTypeID}`);

        const selectedSlot = this.el.querySelector(".o_slot_hours_selected");
        if (!selectedSlot) {
            alert("Please select a slot before confirming.");
            console.warn("No slot selected");
            return;
        }

        // Extract the slot_id and other details
        const slotId = selectedSlot.getAttribute("data-slot-id");
        const startHour = selectedSlot.querySelector("b")?.textContent || "N/A";
        const endHour = selectedSlot.querySelector("t t-if")?.textContent?.trim() || "N/A";

        if (!slotId) {
            alert("Slot ID is missing.");
            console.error("Slot ID is missing in the selected slot element");
            return;
        }

        // Log the slot details to the console
        console.log("Selected Slot Details:");
        console.log(`Slot ID: ${slotId}`);
        console.log(`Start Hour: ${startHour}`);
        console.log(`End Hour: ${endHour}`);

        // Create the submission URL and include the slot_id as a query parameter
        const url = new URL(
            `/appointment/${encodeURIComponent(appointmentTypeID)}/submit`,
            location.origin
        );

        url.searchParams.set("slot_id", slotId);

        // Navigate to the submission URL
        console.log(`Navigating to URL: ${url.href}`);
        document.location = encodeURI(url.href);
    },
});
