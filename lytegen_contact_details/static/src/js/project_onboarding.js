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


    var secondaryInput = document.querySelector("#secondary_contact_phone");
    var itis = window.intlTelInput(secondaryInput,({
        initialCountry: "us"
    }));

    secondaryInput.addEventListener("countrychange", function() {
       document.querySelector("#secondary_country_code").value = itis.getSelectedCountryData().dialCode;
    });

    // Also set initially
    document.querySelector("#secondary_country_code").value = itis.getSelectedCountryData().dialCode;


    $('.js-searchable-select').select2({
        width: '100%',
        placeholder: "Select Sales Consultant",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '40px');

    $('.js-searchable-re-roof').select2({
        placeholder: "Please select one option",
        width: '100%',
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-mount').select2({
        width: '100%',
        placeholder: "Please select mount type",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-mpu').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-hoa').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-gated-access').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-battery').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-utilityBillHolder').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-financeType').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-loanType').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-ppaType').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-installer').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-lead-origin').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');

    $('.js-searchable-addons').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');
});

function onUtilityChange(e){
    if(e.value.toLowerCase() === 'other'){
        $('#utility_company_card').removeClass('col-lg-6');
        $('#utility_bill_card').removeClass('col-lg-6');
        $('#utility_company_card').addClass('col-lg-4');
        $('#utility_bill_card').addClass('col-lg-4');
        $('#utility_bill_input').removeClass('d-none')
        $('#other_utility_bill_holder').prop('required', true);
    }else{
        $('#utility_company_card').removeClass('col-lg-4');
        $('#utility_bill_card').removeClass('col-lg-4');
        $('#utility_company_card').addClass('col-lg-6');
        $('#utility_bill_card').addClass('col-lg-6');
        $('#utility_bill_input').addClass('d-none')
        $('#other_utility_bill_holder').prop('required', false);
    }
}

function onFieldChange(e){
    if(e.value.toLowerCase() === 'yes'){
//        $('#hoa_div').removeClass('col-lg-6');
        $('#gate_code_div').removeClass('col-lg-6');
//        $('#hoa_div').addClass('col-lg-4');
        $('#gate_code_div').addClass('col-lg-6');
        $('#gateCodeBox').removeClass('d-none')
    }else{
//        $('#hoa_div').removeClass('col-lg-6');
        $('#gate_code_div').removeClass('col-lg-6');
//        $('#hoa_div').addClass('col-lg-6');
        $('#gate_code_div').addClass('col-lg-6');
        $('#gateCodeBox').addClass('d-none')
    }
}

function onFinanceChange(e){
    $('#loanHeaderName').html(`${e.value.toUpperCase()} Product`)
    if(e.value === '' || e.value == 'undefined' || e.value.toLowerCase() == 'cash'){
        $('#loan_type_card').addClass('d-none')
        $('#finance_type_card').removeClass('col-lg-6');
        $('#finance_type_card').addClass('col-lg-12');
        $('#loan_type').prop('required', false);
        $('#ppa_type').prop('required', false);
    }else{
        $('#loan_type_card').removeClass('d-none');
        $('#finance_type_card').removeClass('col-lg-12');
        $('#finance_type_card').addClass('col-lg-6');
        if(e.value.toLowerCase() === 'loan'){
            $('#loanDiv').removeClass('d-none');
            $('#ppaDiv').addClass('d-none');
            $('#loan_type').prop('required', true);
            $('#ppa_type').prop('required', false);
        }else if(e.value.toLowerCase() === 'ppa'){
            $('#ppaDiv').removeClass('d-none');
            $('#loanDiv').addClass('d-none');
            $('#loan_type').prop('required', false);
            $('#ppa_type').prop('required', true);
        }

    }
}