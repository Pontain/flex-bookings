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

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("booking-form");
    if (!form) return;

    const dateInput = document.getElementById("booking_date");
    const startHourInput = document.getElementById("start_hour");
    const startMinuteInput = document.getElementById("start_minute");

    if (!dateInput || !startHourInput || !startMinuteInput) return;

    form.addEventListener("submit", (event) => {
        const dateValue = dateInput.value;
        const hourValue = startHourInput.value.padStart(2, "0");
        const minuteValue = startMinuteInput.value.padStart(2, "0");

        if (!dateValue || !hourValue || !minuteValue) return;

        const startDate = new Date(`${dateValue}T${hourValue}:${minuteValue}`);
        const now = new Date();

        if (startDate < now) {
            const confirmed = confirm(
                "Starttiden ligger bakåt i tiden.\n\nVill du ändå skapa bokningen?"
            );

            if (!confirmed) {
                event.preventDefault();
            }
        }
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const startDateInput = document.getElementById("start_date");
    const endDateInput = document.getElementById("end_date");

    if (!startDateInput || !endDateInput) {
        return;
    }

    startDateInput.addEventListener("change", () => {
        endDateInput.min = startDateInput.value;

        if (!endDateInput.value || endDateInput.value < startDateInput.value) {
            endDateInput.value = startDateInput.value;
        }
    });
});