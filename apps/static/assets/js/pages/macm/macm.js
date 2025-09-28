$(document).ready(function() {

    // Collapse all cards
    $('.card-header.collapsed').each(function() {
        $(this).parent('.card').find('.collapse').collapse('hide');
        $(this).parent('.card').find('.collapse').removeClass('show');
    });

    $('#uploadMacmForm').submit(function(e) {
        e.preventDefault();
        $('.upload_macm').addClass('btn-loading');
        let formData = new FormData(this);
        $.ajax({
            url: '/api/upload_macm',
            type: 'POST',
            data: formData,
            enctype: 'multipart/form-data',
            processData: false,
            contentType: false,
            cache: false,
        }).done(function(response) {
            location.reload();
        }).fail(function(response) {
            $('.upload_macm').removeClass('btn-loading');
            showModal("Upload failed", JSON.parse(response.responseText));
        });
    });

    $('#uploadDockerComposeForm').submit(function(e) {
        e.preventDefault();
        $('.upload_docker_compose').addClass('btn-loading');
        let formData = new FormData(this);
        $.ajax({
            url: '/api/upload_docker_compose',
            type: 'POST',
            data: formData,
            enctype: 'multipart/form-data',
            processData: false,
            contentType: false,
            cache: false,
        }).done(function(response) {
            $('.upload_docker_compose').removeClass('btn-loading');
            showDC2MModal(response.app_name + " MACM", response.cypher, response.app_name, response.services, response.service_types, response.suggested_asset_types);
        }).fail(function(response) {
            $('.upload_docker_compose').removeClass('btn-loading');
            showModal("Upload failed", JSON.parse(response.responseText));
        });
    });

    $('#uploadDC2MOutput').click(function() {
        $(this).addClass('btn-loading');
        let cypher = $('#modalDC2MOutput').text();
        if (cypher) {
            let formData = new FormData();
            formData.append('macmAppName', $('#uploadDC2MOutput').attr('data-app-name'));
            formData.append('macmCypher', cypher);
            $.ajax({
                url: '/api/upload_macm',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false
            }).done(function(response) {
                location.reload();
            }).fail(function(response) {
                $(this).removeClass('btn-loading');
                $('#modalDC2M').modal('hide');
                showModal("Upload failed", JSON.parse(response.responseText), autohide = true);
            });
        }
    });

    $('#editMacmModal').on('show.bs.modal', function(event) {
        const AppID = event.relatedTarget.getAttribute('data-bs-AppID');
        const AppName = event.relatedTarget.getAttribute('data-bs-AppName');
        this.querySelector('#editAppID').value = AppID;
        this.querySelector('#editAppName').textContent = AppName;
    });

    $('#editMacmSubmit').click(function() {
        const AppID = $('#editAppID').val();
        const QueryCypher = $('#editQueryCypher').val();
        editMacm(AppID, QueryCypher);
    });

    $('#deleteModal').on('show.bs.modal', function(event) {
        const AppID = event.relatedTarget.dataset.bsAppid;
        const AppName = event.relatedTarget.dataset.bsAppname;
        $('#deleteName').text(AppName);
        $('#deleteConfirm').click(function() { deleteMacm(AppID); });
        this.querySelector('#deleteID').value = AppID;
    });
});

function deleteMacm(AppID) {
    var formData = new FormData();
    formData.append('AppID', AppID);
    $.ajax({
        url: '/api/delete_macm',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false
    }).done(function(response) {
        location.reload();
    }).fail(function(response) {
        $('#deleteModal').modal('hide');
        showModal("Delete failed", JSON.parse(response.responseText), autohide = true);
    });
}

function showDC2MModal(title, cypher, app_name, services, service_types, suggested_asset_types) {
    $('#modalDC2MLabel').text(title);
    if (cypher) {
        $('#modalDC2MOutput').text(cypher);
        $('#modalDC2MOutputPre').show();
        $('#modalDC2MAlert').hide();
        $('#uploadDC2MOutput').attr('data-app-name', app_name);
        $('#uploadDC2MOutput').show();
        $('#copyDC2MOutput').show();
        $('#copyDC2MOutput').attr('data-clipboard-text', cypher);

        // Populate services customization
        let servicesList = $('#modalDC2MServicesList');
        servicesList.empty();
        services.forEach(service => {
            let serviceTypeOptions = service_types.map(service_type => {
                return `<option value="${service_type.name}" ${service_type.name === suggested_asset_types[service][0] ? 'selected' : ''}>PL: ${service_type.primary_label}, SL: ${service_type.secondary_label}, Asset Type: ${service_type.name} ${suggested_asset_types[service].includes(service_type.name ) ? '⭐️' : ''}</option>`;
            }).join('');
            let serviceItem = `
                <div class="mb-3">
                    <label for="service_${service}" class="form-label">${service}</label>
                    <select class="form-select" id="service_${service}">
                        ${serviceTypeOptions}
                    </select>
                </div>
            `;
            servicesList.append(serviceItem);
        });
        updateDC2MOutput(services, service_types);
    } else {
        $('#modalDC2MOutputPre').hide();
        $('#modalDC2MAlert').show();
        $('#uploadDC2MOutput').hide();
        $('#copyDC2MOutput').hide();
    }

    $('#modalDC2MServicesList').on('change', 'select', function() {
        updateDC2MOutput(services, service_types);
    });

    $('#modalDC2M').modal('show');
    Prism.highlightAll();
    $('.upload_macm').removeClass('btn-loading');
}

function updateDC2MOutput(services, service_types) {
    let cypher = $('#modalDC2MOutput').text();
    services.forEach(service => {
        let selectedType = $(`#service_${service}`).val();
        let primaryLabel = service_types.find(st => st.name === selectedType)?.primary_label || 'Service';
        let secondaryLabel = service_types.find(st => st.name === selectedType)?.secondary_label || '';
        
        let regex = new RegExp(`(:[A-Za-z0-9_]+(?::[A-Za-z0-9_]+)?)\\s*\\{([^}]*name:\\s*['"]${service}['"][^}]*)\\}`, 'g');
        let newLabel = secondaryLabel ? `:${primaryLabel}:${secondaryLabel}` : `:${primaryLabel}`;

        cypher = cypher.replace(regex, function(match, labelPart, props) {
            let newProps;
            if (/type:\s*'[^']*'/.test(props)) {
                newProps = props.replace(/type:\s*'[^']*'/, `type: '${selectedType}'`);
            } else {
                newProps = props.replace(/(name:\s*['"][^'"]+['"])/, `$1, type: '${selectedType}'`);
            }
            return `${newLabel} {${newProps}}`;
        });
    });
    $('#modalDC2MOutput').text(cypher);
    $('#copyDC2MOutput').attr('data-clipboard-text', cypher);
    Prism.highlightAll();
}