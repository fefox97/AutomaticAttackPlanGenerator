$(document).ready(function() {
    getAllCommands();
    $('.command-input').on('change', function() {
        getAllCommands();
    });

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
    $('.command').children('button').click(copySingleCommand);
    $('#copyAllCommands').click(copyAllCommands);
    $('.bg-capec').click(function() {
        window.open($(this).attr('href'), '_blank');
    });
});

function copySingleCommand(element) {
    let command = '';
    $(this).parent('.command').find('.command-input').each(function(el) {
        if(this.nodeName == 'SPAN') {
            command += $(this).text();
        }
        else if(this.nodeName == 'INPUT') {
            let value = $(this).val();
            if(value == '') {
                value = $(this).attr('placeholder');
            }
            command += value;
        }
    });
    navigator.clipboard.writeText(command);
}

function getAllCommands(){
    let commands = [];
    $('.command').each(function() {
        let command = '';
        $(this).find('.command-input').each(function(el) {
            if(this.nodeName == 'SPAN') {
                command += $(this).text();
            }
            else if(this.nodeName == 'INPUT') {
                let value = $(this).val();
                if(value == '') {
                    value = $(this).attr('placeholder');
                }
                command += value;
            }
        });
        commands.push(command);
    });
    commands = Array.from(new Set(commands));
    $('#allCommands').text(commands.join('\n'));
    window.Prism.highlightAll();
}

function copyAllCommands() {
    navigator.clipboard.writeText($('#allCommands').text());
}

function downloadAllCommands(filename){
    const link = document.createElement("a");
    let blob = new Blob([$('#allCommands').text()], {type: "text/plain;charset=utf-8"});
    link.href = URL.createObjectURL(blob);
    link.download = filename || "commands.sh";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}