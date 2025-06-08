/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.appointmentForm = publicWidget.registry.appointmentForm.extend({
    /**
     * Override the _onConfirmAppointment method.
     */
    _onConfirmAppointment: async function (event) {
        // Log the phone input value
        const phoneInput = this.el.querySelector('input[name="phone"]');
        if (phoneInput) {
            console.log("Phone value:", phoneInput.value);
        } else {
            console.log("Phone input field not found.");
        }

        // Log the test input value
        const testInput = this.el.querySelector('input[name="test_field"]');
        if (testInput) {
            console.log("Test value:", testInput.value);
        } else {
            console.log("Test input field not found.");
        }

        // Log the selected language value
//        const languageSelect = this.el.querySelector('select[name="language"]');
//        if (languageSelect) {
//            const selectedLanguage = languageSelect.value;
//            if (selectedLanguage) {
//                console.log("Selected Language:", selectedLanguage);
//            } else {
//                console.log("No language selected.");
//            }
//        } else {
//            console.log("Language dropdown field not found.");
//        }
        const languageSelect = this.el.querySelector('select[name="language"]');
        if (languageSelect) {
            const selectedLanguage = languageSelect.value;
            if (selectedLanguage) {
                console.log("Selected Language:", selectedLanguage);
                // Proceed with further logic here
            } else {
                console.error("No language selected. Please choose a language.");
                // Display an error message to the user
                alert("Please choose a language before proceeding.");
            }
        } else {
            console.error("Language dropdown field not found.");
        }


        // Log the average bill value
        const averageBillInput = this.el.querySelector('input[name="average_bill"]');
        if (averageBillInput) {
            console.log("Average Bill value:", averageBillInput.value);
        } else {
            console.log("Average Bill input field not found.");
        }

        // Log the address_2 value
        const addressInput = this.el.querySelector('input[name="address"]');
        if (addressInput) {
            console.log("Address value:", addressInput.value);
        } else {
            console.log("Address input field not found.");
        }

        // Log the state_2 value
        const stateInput = this.el.querySelector('input[name="state"]');
        if (stateInput) {
            console.log("State value:", stateInput.value);
        } else {
            console.log("State input field not found.");
        }

        // Log the city_2 value
        const cityInput = this.el.querySelector('input[name="city"]');
        if (cityInput) {
            console.log("City value:", cityInput.value);
        } else {
            console.log("City input field not found.");
        }

        // Log the postal_code_2 value
        const postalCodeInput = this.el.querySelector('input[name="zip_code"]');
        if (postalCodeInput) {
            console.log("Postal Code value:", postalCodeInput.value);
        } else {
            console.log("Postal Code input field not found.");
        }

        // Log the opener_2 value
        const openerInput = this.el.querySelector('input[name="opener"]');
        if (openerInput) {
            console.log("Opener value:", openerInput.value);
        } else {
            console.log("Opener input field not found.");
        }

        // Log the setter_2 value
        const setterInput = this.el.querySelector('input[name="setter"]');
        if (setterInput) {
            console.log("Setter value:", setterInput.value);
        } else {
            console.log("Setter input field not found.");
        }

        // Log the sales_consultant_2 value
        const salesConsultantInput = this.el.querySelector('input[name="sales_consultant"]');
        if (salesConsultantInput) {
            console.log("Sales Consultant value:", salesConsultantInput.value);
        } else {
            console.log("Sales Consultant input field not found.");
        }

        // Log the appointment_notes value
        const appointmentNotesInput = document.querySelector('input[name="appointment_notes"]');
        if (appointmentNotesInput) {
            console.log("Appointment Notes value:", appointmentNotesInput.value);
        } else {
            console.log("Appointment Notes textarea not found.");
        }

        // Call the original method to retain existing functionality
        await this._super.apply(this, arguments);
    },
});
