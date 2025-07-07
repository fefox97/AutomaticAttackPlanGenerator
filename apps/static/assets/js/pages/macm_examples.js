$(document).ready(function () {
    // Initialize the highlight.js library
    hljs.highlightAll();
    $('#copy-cypher-btn').on('click', function () {
        var code = document.getElementById('cypher-query').innerText;
        navigator.clipboard.writeText(code).then(function() {
            // Optional: feedback to user
        });
    });
});