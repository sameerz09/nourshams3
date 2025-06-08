document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ Credit Check JS Loaded");

    const phoneInput = document.querySelector("#phone");
    const eventIdInput = document.querySelector("#latest_event_id");
    const designSelect = document.querySelector("#selected_design_id");

    if (!phoneInput) console.warn("❌ Phone input with ID #phone not found!");
    if (!eventIdInput) console.warn("❌ Input with ID #latest_event_id not found!");
    if (!designSelect) console.warn("❌ Select element with ID #selected_design_id not found!");

    if (!phoneInput || !eventIdInput || !designSelect) return;

    phoneInput.addEventListener("blur", async () => {
        const phone = phoneInput.value.trim();
        if (!phone) {
            console.warn("⚠️ Phone number is empty.");
            return;
        }

        console.log("📞 Fetching data for phone:", phone);

        try {
            const response = await fetch("/calendar/latest_event_by_phone", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ phone }),
            });

            console.log("🔁 Fetch Response:", response);

            const data = await response.json();
            console.log("📬 Backend returned:", data);

            const eventId = data.result?.latest_event_id || 0;
            const designOptions = data.result?.design_options || [];

            // Update Event ID
            eventIdInput.value = eventId !== 0 ? eventId : "No event found";

            // Populate Design Dropdown
            designSelect.innerHTML = '<option value="">-- Select Design --</option>';

            if (designOptions.length > 0) {
                designOptions.forEach(option => {
                    const opt = document.createElement("option");
                    opt.value = option.id;
                    opt.textContent = option.name || option.display_name || `Design ${option.id}`;
                    designSelect.appendChild(opt);
                });
            } else {
                const noOpt = document.createElement("option");
                noOpt.value = "";
                noOpt.textContent = "No designs available";
                designSelect.appendChild(noOpt);
            }

        } catch (error) {
            console.error("❌ Error fetching event data:", error);
            eventIdInput.value = "Error fetching event";
            designSelect.innerHTML = '<option value="">Error loading designs</option>';
        }
    });

    // Optional: On form submit, attach selected design name to a hidden input (if needed)
    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", () => {
            const selectedOption = designSelect.options[designSelect.selectedIndex];
            const selectedDesignName = selectedOption ? selectedOption.textContent : "";

            let hiddenInput = document.querySelector("input[name='selected_design_name']");
            if (!hiddenInput) {
                hiddenInput = document.createElement("input");
                hiddenInput.type = "hidden";
                hiddenInput.name = "selected_design_name";
                form.appendChild(hiddenInput);
            }

            hiddenInput.value = selectedDesignName;
        });
    }
});
