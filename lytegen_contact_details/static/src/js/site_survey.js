$(document).ready(function() {
    $('.js-searchable-select').select2({
        width: '100%',
        placeholder: "Please select one option",
        allowClear: true
    }).next('.select2-container').find('.select2-selection--single').css('height', '35px');
})


function onFieldChange(e,id){
    if(e.value === "Yes"){
        $(`#${id}`).removeClass('d-none');
    }else{
        $(`#${id}`).addClass('d-none');
    }
}