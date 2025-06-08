document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ Credentials JS Loaded");

    const positionSelect = document.querySelector("#applied_position");

    if (!positionSelect) {
        console.warn("❌ Select element with ID #applied_position not found!");
        return;
    }

    const fetchJobPositions = async () => {
        console.log("📤 Sending POST request to fetch job positions...");

        try {
            const response = await fetch("/credentials/job_positions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ request: "job_positions" }) // dummy payload
            });

            console.log("🔁 Fetch Response:", response);

            const data = await response.json();
            console.log("📬 Backend returned:", data);

            const jobPositions = data.result?.job_positions || [];

            // Populate the dropdown
            positionSelect.innerHTML = '<option value="">-- Select Position --</option>';

            if (jobPositions.length > 0) {
                jobPositions.forEach(job => {
                    const option = document.createElement("option");
                    option.value = job.name;
                    option.textContent = job.name;
                    positionSelect.appendChild(option);
                });
            } else {
                const noOpt = document.createElement("option");
                noOpt.value = "";
                noOpt.textContent = "No positions available";
                positionSelect.appendChild(noOpt);
            }

        } catch (error) {
            console.error("❌ Error fetching job positions:", error);
            positionSelect.innerHTML = '<option value="">Error loading positions</option>';
        }
    };

    // Fetch job titles on page load
    fetchJobPositions();

    // Optional: Add selected job name to a hidden input on submit
    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", () => {
            const selectedOption = positionSelect.options[positionSelect.selectedIndex];
            const selectedPositionName = selectedOption ? selectedOption.textContent : "";

            let hiddenInput = document.querySelector("input[name='selected_position_name']");
            if (!hiddenInput) {
                hiddenInput = document.createElement("input");
                hiddenInput.type = "hidden";
                hiddenInput.name = "selected_position_name";
                form.appendChild(hiddenInput);
            }

            hiddenInput.value = selectedPositionName;
        });
    }
});
