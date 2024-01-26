const DarkModeButton = document.getElementById('DarkMode');

function turnOnDarkMode() {
    localStorage.setItem('dark_mode', 'true');
    document.documentElement.setAttribute('data-bs-theme', 'dark');
    DarkModeButton.classList.add('active');
}

function turnOffDarkMode() {
    localStorage.setItem('dark_mode', 'false');
    document.documentElement.setAttribute('data-bs-theme', 'light');
    DarkModeButton.classList.remove('active');
}


localStorage.getItem('dark_mode') == 'true' ? turnOnDarkMode() : turnOffDarkMode();

document.getElementById('DarkMode').addEventListener('click', () => {
    localStorage.getItem('dark_mode') == 'true' ? turnOffDarkMode() : turnOnDarkMode();
});
