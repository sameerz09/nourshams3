/** @odoo-module **/

import { Component, useRef, onMounted, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class AddressAutocomplete extends Component {
    static template = xml`
        <div>
            <input type="text" t-ref="inputRef" class="o_address_autocomplete form-control" placeholder="Enter address"/>
        </div>
    `;

    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.inputRef = useRef("inputRef");

        onMounted(() => {
            // 🟡 Set initial value from the database into the input
            const currentValue = this.props.record.data[this.props.name];
            if (currentValue && this.inputRef.el) {
                this.inputRef.el.value = currentValue;
            }

            // Load Google API and initialize autocomplete
            this.loadGoogleMapsAPI().then(() => {
                this.initAutocomplete();
            }).catch(err => {
                console.error("Google Maps API failed to load:", err);
            });
        });
    }

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
    }

    initAutocomplete() {
        if (typeof google !== "undefined") {
            const input = this.inputRef.el;

            const autocomplete = new google.maps.places.Autocomplete(input, {
                types: ["geocode"],
                componentRestrictions: { country: "US" },
            });

            autocomplete.addListener("place_changed", () => {
                const place = autocomplete.getPlace();
                if (place.geometry) {
                    const updates = {};
                    const components = place.address_components || [];
                    const existingFields = this.props.record.data;

                    // Extract specific components
                    for (const comp of components) {
                        const types = comp.types;

                        if (types.includes("street_number")) {
                            updates._street_number = comp.long_name;
                        }
                        if (types.includes("route")) {
                            updates._route = comp.long_name;
                        }
                        if (types.includes("locality") && "city" in existingFields) {
                            updates["city"] = comp.long_name;
                        }
                        if (types.includes("administrative_area_level_1") && "state" in existingFields) {
                            updates["state"] = comp.short_name;
                        }
                        if (types.includes("postal_code") && "postal_code" in existingFields) {
                            updates["postal_code"] = comp.long_name;
                        }
                    }

                    // Combine street_number and route into street
                    if ("street" in existingFields) {
                        const street = [updates._street_number, updates._route].filter(Boolean).join(" ");
                        updates["street"] = street;
                        input.value = street;
                    }

                    // Optionally store the full address in the main field
                    if (this.props.name in existingFields) {
                        updates[this.props.name] = updates["street"];
                    }

                    delete updates._street_number;
                    delete updates._route;

                    this.props.record.update(updates);
                }
            });

            // 📌 Handle manual typing + blur
            input.addEventListener("blur", () => {
                const typedAddress = input.value;
                const currentValue = this.props.record.data[this.props.name];

                if (typedAddress && typedAddress !== currentValue) {
                    this.props.record.update({
                        [this.props.name]: typedAddress,
                    });
                }
            });
        }
    }
}

export const addressAutocomplete = {
    component: AddressAutocomplete,
    displayName: "Address Autocomplete",
};

registry.category("fields").add("address_autocomplete", addressAutocomplete);
