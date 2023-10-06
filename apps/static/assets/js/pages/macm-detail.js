$(document).ready(function() {
    $('#ExpandToggle').prop('checked', false);
    $('#ExpandToggle').on('click', function() {
        if ($(this).hasClass('active')) {
            $("#accordionOne .collapse").collapse('show');
        } else {
            $("#accordionOne .collapse").collapse('hide');
        }
    });
    $("#accordionOne [aria-expanded='false']").each(function() {
        $(this).closest('.accordion-item').children('.collapse').collapse('hide');
    });
    $('.command').children('button').click(function() {
        var command = '';
        $(this).parent('.command').find('.command-input').each(function(el) {
            if(this.nodeName == 'SPAN') {
                command += $(this).text();
            }
            else if(this.nodeName == 'INPUT') {
                var value = $(this).val();
                if(value == '') {
                    value = $(this).attr('placeholder');
                }
                command += value;
            }
        });
        navigator.clipboard.writeText(command);
    });
});



