$(document).ready(function() {
    const form = document.getElementById('questionnaire-form');
    if (!form) return;

    const submitButton = document.querySelector('button[type="submit"]');
    console.log(submitButton);
    if (!submitButton) return;

    function validateForm() {
        const inputs = form.querySelectorAll('input[type="radio"], input[type="checkbox"]');
        const questionNames = [...new Set([...inputs].map(input => input.name))];

        const allAnswered = questionNames.every(name => {
            return [...form.querySelectorAll(`[name='${name}']`)].some(input => input.checked);
        });

        submitButton.disabled = !allAnswered;
        submitButton.classList.toggle('btn-success', allAnswered);
        submitButton.setAttribute('aria-disabled', !allAnswered);
    }

    form.addEventListener('input', validateForm);

    validateForm();
});