$(document).ready(function() {
    $('#ExpandToggle').prop('checked', false);
    $('#ExpandToggle').on('change', function() {
        if ($(this).is(':checked')) {
            $('.card-header[data-bs-toggle="collapse"]').parent('.card').find('.collapse').collapse('show');
        } else {
            $('.card-header[data-bs-toggle="collapse"]').parent('.card').find('.collapse').collapse('hide');
        }
    });
    $('.card-header.collapsed').each(function() {
        $(this).parent('.card').find('.collapse').collapse('hide');
        $(this).parent('.card').find('.collapse').removeClass('show');
    });
});



