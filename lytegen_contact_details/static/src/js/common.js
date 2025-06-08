$(document).ready(function() {
    var input = document.querySelector("#phone");
    var iti = window.intlTelInput(input,({
        initialCountry: "us"
    }));

    input.addEventListener("countrychange", function() {
       document.querySelector("#country_code").value = iti.getSelectedCountryData().dialCode;
    });

    // Also set initially
    document.querySelector("#country_code").value = iti.getSelectedCountryData().dialCode;

})