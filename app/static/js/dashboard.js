function formatDayLabel(date) {
    return date.toLocaleDateString("sv-SE", {
        weekday: "long",
        day: "numeric",
        month: "short"
    });
}

function formatTime(dateString) {
    const d = new Date(dateString);
    return d.toLocaleTimeString("sv-SE", {
        hour: "2-digit",
        minute: "2-digit"
    });
}

/* =========================
   Modal-funktionalitet
========================= */

async function openBookingModal(bookingId) {
    const overlay = document.getElementById("booking-modal-overlay");
    const content = document.getElementById("booking-modal-content");

    if (!overlay || !content) {
        console.error("Modal-elementen hittades inte i DOM.");
        return;
    }

    overlay.classList.remove("hidden");
    content.innerHTML = "<p>Laddar...</p>";

    try {
        const response = await fetch(`/bookings/${bookingId}/modal`);

        if (!response.ok) {
            content.innerHTML = "<p>Kunde inte hämta bokningsdetaljer.</p>";
            return;
        }

        const html = await response.text();
        content.innerHTML = html;
    } catch (error) {
        content.innerHTML = "<p>Ett fel uppstod när bokningen skulle hämtas.</p>";
        console.error(error);
    }
}

function closeBookingModal() {
    const overlay = document.getElementById("booking-modal-overlay");
    const content = document.getElementById("booking-modal-content");

    if (!overlay || !content) {
        return;
    }

    overlay.classList.add("hidden");
    content.innerHTML = "";
}

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
        closeBookingModal();
    }
});

async function loadDashboardCalendar() {
    const config = window.dashboardCalendarConfig;

    const response = await fetch(
        `/calendar/events?start=${encodeURIComponent(config.start)}&end=${encodeURIComponent(config.end)}`
    );

    const events = await response.json();
    renderDashboardCalendar(config.start, events);
}

function renderDashboardCalendar(startString, events) {
    const container = document.getElementById("dashboard-calendar");
    if (!container) {
        return;
    }

    container.innerHTML = "";

    const weekStart = new Date(startString);

    for (let i = 0; i < 7; i++) {
        const dayDate = new Date(weekStart);
        dayDate.setDate(dayDate.getDate() + i);

        const column = document.createElement("div");
        column.className = "dashboard-day";

        const header = document.createElement("div");
        header.className = "dashboard-day-header";
        header.textContent = formatDayLabel(dayDate);

        const body = document.createElement("div");
        body.className = "dashboard-day-body";

        const dayEvents = events
            .filter(event => {
                const eventStart = new Date(event.start);
                return eventStart.toDateString() === dayDate.toDateString();
            })
            .sort((a, b) => new Date(a.start) - new Date(b.start));

        if (dayEvents.length === 0) {
            const empty = document.createElement("div");
            empty.className = "dashboard-empty";
            empty.textContent = "Inga bokningar";
            body.appendChild(empty);
        } else {
            dayEvents.forEach(event => {
                const card = document.createElement("button");
                card.type = "button";
                card.className = "dashboard-booking-card";
                card.onclick = () => openBookingModal(event.id);

                if (event.venue_color) {
                    card.style.borderLeftColor = event.venue_color;
                }

                card.innerHTML = `
                    <div class="booking-title">${event.title}</div>
                    <div class="booking-time">${formatTime(event.start)} - ${formatTime(event.end)}</div>
                    <div class="booking-contact">${event.contact_name ?? ""}</div>
                `;

                body.appendChild(card);
            });
        }

        column.appendChild(header);
        column.appendChild(body);
        container.appendChild(column);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadDashboardCalendar();
});