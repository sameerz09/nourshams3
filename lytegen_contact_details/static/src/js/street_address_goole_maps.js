/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AppointmentForm = publicWidget.Widget.extend({
    selector: "#serviceAddress", // Ensure this matches your form's class
    start: function () {
        this._super.apply(this, arguments);
        console.log("Appointment Form Loaded Successfully");

        this.loadGoogleMapsAPI().then(() => {
            this.initAutocomplete();
        }).catch(err => {
            console.error("Google Maps API failed to load:", err);
        });
    },

    async loadGoogleMapsAPI() {
        if (typeof google !== "undefined" && google.maps) {
            return;
        }

        return new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyDT7UtvJCB2HNgn-MRvz1rT1uAcmnyXC84&libraries=places`;
            script.async = true;
            script.defer = true;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    },

    initAutocomplete() {
        if (typeof google !== "undefined") {
            console.log("Google Maps Autocomplete Initialized111111111111111");
            const streetAddressInput = this.el.querySelector('input[name="street_address"]');
            const cityInput = this.el.querySelector('input[name="city"]');
            const stateInput = this.el.querySelector('input[name="state"]');
            const zipCodeInput = this.el.querySelector('input[name="zipcode"]') || this.el.querySelector('input[name="zip_code"]');


            if (streetAddressInput) {
                const autocomplete = new google.maps.places.Autocomplete(streetAddressInput, {
                    types: ["geocode"],
                    componentRestrictions: { country: "US" },
                });

                autocomplete.addListener("place_changed", () => {
                            const place = autocomplete.getPlace();
                            if (place.geometry) {
                                console.log("Selected Address:", place.formatted_address);

                                // Reset values before extracting
                                streetAddressInput.value = "";
                                cityInput.value = "";
                                stateInput.value = "";
                                zipCodeInput.value = "";

                                let streetNumber = "";
                                let route = "";

                                place.address_components.forEach(component => {
                                    console.log(`Type: ${component.types.join(", ")}, Long Name: ${component.long_name}, Short Name: ${component.short_name}`);
                                });

                                // Extract address components
                                place.address_components.forEach(component => {
                                    const types = component.types;

                                    if (types.includes("street_number")) {
                                        streetNumber = component.long_name;
                                    }
                                    if (types.includes("route")) {
                                        route = component.long_name;
                                    }
                                    if (types.includes("locality")) {
                                        cityInput.value = component.long_name; // City
                                    }
                                    if (types.includes("administrative_area_level_1")) {
                                        stateInput.value = component.short_name; // State
                                    }
                                    if (types.includes("postal_code")) {
                                        zipCodeInput.value = component.long_name; // Zip Code
                                    }
                                });

                                // Set only the street address
                                streetAddressInput.value = `${streetNumber} ${route}`.trim();

                                console.log("Street Address:", streetAddressInput.value);
                                console.log("City:", cityInput.value);
                                console.log("State:", stateInput.value);
                                console.log("Zip Code:", zipCodeInput.value);
                            }
                        });

            } else {
                console.error("Street Address input field not found.");
            }
        }
    }
});
