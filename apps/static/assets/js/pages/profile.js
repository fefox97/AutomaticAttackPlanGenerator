function loadTokens() {
    fetch('/api/api_tokens')
        .then(response => {
            if (response.status === 403) {
                throw new Error('You do not have permission to view API tokens.');
            }
            return response.json();
        })
        .then(tokens => {
            const tbody = document.querySelector('#tokenTable tbody');
            tbody.innerHTML = '';
            if (tokens.length === 0) {
                document.getElementById('noTokensAlert').style.display = 'block';
                document.getElementById('tokenTable').style.display = 'none';
                return;
            }
            document.getElementById('noTokensAlert').style.display = 'none';
            document.getElementById('tokenTable').style.display = '';
            tokens.forEach(token => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${token.id}</td>
                    <td>${token.description || ''}</td>
                    <td>
                        <span class="token-value"><code>${token.token}</code></span>
                        <button class="btn btn-link btn-sm p-0 ms-2" onclick="copyToken('${token.token}', this)" title="Copy token">
                            <i class="bi bi-clipboard"></i>
                        </button>
                    </td>
                    <td>${token.created_on}</td>
                    <td>${token.expires_on}</td>
                    <td>${token.revoked ? '<span class=\"badge bg-danger\">Revoked</span>' : '<span class=\"badge bg-success\">Active</span>'}</td>
                    <td>
                        ${!token.revoked ? `<button class=\"btn btn-sm btn-warning\" onclick=\"revokeToken(${token.id})\">Revoke</button>` : `<button class=\"btn btn-sm btn-danger\" onclick=\"deleteToken(${token.id})\">Delete</button>`}
                    </td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(error => {
            console.error('Error loading tokens:', error);
        });
}

function copyToken(token, btn) {
    navigator.clipboard.writeText(token).then(function() {
        btn.innerHTML = '<i class="bi bi-clipboard-check"></i>';
        setTimeout(() => {
            btn.innerHTML = '<i class="bi bi-clipboard"></i>';
        }, 1500);
    });
}

function revokeToken(tokenId) {
    if (!confirm('Are you sure you want to revoke this token?')) return;
    fetch(`/api/api_tokens/${tokenId}/revoke`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        loadTokens();
    });
}

function deleteToken(tokenId) {
    if (!confirm('Are you sure you want to delete this token?')) return;
    fetch(`/api/api_tokens/${tokenId}/delete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        loadTokens();
    });
}

// Load tokens every time the modal is opened
$('#tokenManagerModal').on('show.bs.modal', function () {
    loadTokens();
    document.getElementById('tokenCreatedAlert').style.display = 'none';
});

// Handle token generation
$('#generateTokenForm').on('submit', function(e) {
    e.preventDefault();
    const expiresDays = $('#expiresDays').val();
    const description = $('#tokenDescription').val();
    if (!description) {
        $('#tokenDescription').addClass('is-invalid');
        return;
    } else {
        $('#tokenDescription').removeClass('is-invalid');
    }
    fetch('/api/api_tokens', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ expires_days: expiresDays, description: description })
    })
    .then(response => {
        if (response.status === 403) {
            throw new Error('You do not have permission to create API tokens.');
        } else {
            throw new Error('Error generating token. Please try again.');
        }
        return response.json();
    })
    .then(data => {
        loadTokens();
        $('#tokenCreatedAlert').text('Token generated: ' + data.token).show();
        $('#expiresDays').val('');
        $('#tokenDescription').val('');
        setTimeout(() => {
            $('#tokenCreatedAlert').fadeOut();
        }, 8000);
    })
    .catch(error => {
        alert(error.message);
    });
});