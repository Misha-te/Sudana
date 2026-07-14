(function () {
    function applyStoredTheme() {
        document.documentElement.classList.toggle("dark", localStorage.getItem("darkMode") === "on");
    }
    applyStoredTheme();
    window.addEventListener("storage", function (event) {
        if (event.key === "darkMode") applyStoredTheme();
    });
    window.sudanaApplyTheme = applyStoredTheme;
})();
