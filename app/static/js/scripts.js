document.addEventListener("click", function (e) {

    const row = e.target.closest(".clickable-row");
    if (!row) return;

    if (e.target.closest("a")) return;

    const href = row.getAttribute("data-href");
    if (href) window.location.href = href;

});

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".clickable-row[data-href]").forEach(row => {
        row.addEventListener("click", (event) => {
            if (event.target.closest("a, button, form, input")) {
                return;
            }

            window.location.href = row.dataset.href;
        });
    });
});