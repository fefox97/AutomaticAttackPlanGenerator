const CountUp = window.countUp.CountUp;

$(document).ready(function() {
    animateCountUp('count-up');
});

function animateCountUp(elementClass) {
    const element = document.getElementsByClassName(elementClass);
    for (let i = 0; i < element.length; i++) {
        if (element[i]) {
            let endValue = parseInt(element[i].textContent, 10);
            const countUp = new CountUp(element[i], endValue);
            if (!countUp.error) {
                countUp.start();
            } else {
                console.error(countUp.error);
            }
        } else {
            console.warn(`Element with class ${elementClass} not found.`);
        }
    }
}