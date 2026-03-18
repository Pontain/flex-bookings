document.addEventListener("click", function (e) {

    const row = e.target.closest(".clickable-row");
    if (!row) return;

    if (e.target.closest("a")) return;

    const href = row.getAttribute("data-href");
    if (href) window.location.href = href;

});