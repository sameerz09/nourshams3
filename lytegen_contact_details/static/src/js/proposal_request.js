$(document).ready(function() {

    var input = document.querySelector("#customer_phone");
    var iti = window.intlTelInput(input,({
        initialCountry: "us"
    }));

    input.addEventListener("countrychange", function() {
       document.querySelector("#country_code").value = iti.getSelectedCountryData().dialCode;
    });

    // Also set initially
    document.querySelector("#country_code").value = iti.getSelectedCountryData().dialCode;

    $('.js-searchable-select').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

});
