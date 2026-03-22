let currentDate = new Date();

function startOfWeek(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = day === 0 ? -6 : 1 - day; // måndag som första dag
    d.setDate(d.getDate() + diff);
    d.setHours(0, 0, 0, 0);
    return d;
}

function endOfWeek(date) {
    const d = startOfWeek(date);
    d.setDate(d.getDate() + 7);
    return d;
}

function formatDateLabel(date) {
    return date.toLocaleDateString("sv-SE", {
        weekday: "long",
        day: "numeric",
        month: "short"
    });
}

function formatWeekLabel(startDate) {
    const endDate = new Date(startDate);
    endDate.setDate(endDate.getDate() + 6);

    return `${startDate.toLocaleDateString("sv-SE")} - ${endDate.toLocaleDateString("sv-SE")}`;
}

function formatTime(dateString) {
    return new Date(dateString).toLocaleTimeString("sv-SE", {
        hour: "2-digit",
        minute: "2-digit"
    });
}

async function loadCalendar() {
    const weekStart = startOfWeek(currentDate);
    const weekEnd = endOfWeek(currentDate);

    document.getElementById("week-label").textContent = formatWeekLabel(weekStart);

    const response = await fetch(
        `/calendar/events?start=${encodeURIComponent(weekStart.toISOString())}&end=${encodeURIComponent(weekEnd.toISOString())}`
    );

    const events = await response.json();
    renderCalendar(weekStart, events);
}

function renderCalendar(weekStart, events) {
    const grid = document.getElementById("calendar-grid");
    grid.innerHTML = "";

    for (let i = 0; i < 7; i++) {
        const dayDate = new Date(weekStart);
        dayDate.setDate(dayDate.getDate() + i);

        const dayColumn = document.createElement("div");
        dayColumn.className = "calendar-day";

        const today = new Date();
        if (dayDate.toDateString() === today.toDateString()) {
        dayColumn.classList.add("today");
        }

        const header = document.createElement("div");
        header.className = "calendar-day-header";
        header.textContent = formatDateLabel(dayDate);

        const body = document.createElement("div");
        body.className = "calendar-day-body";

        const dayEvents = events
            .filter(event => {
                const eventStart = new Date(event.start);
                return eventStart.toDateString() === dayDate.toDateString();
            })
            .sort((a, b) => new Date(a.start) - new Date(b.start));

        if (dayEvents.length === 0) {
            const empty = document.createElement("div");
            empty.className = "calendar-empty";
            empty.textContent = "Inga bokningar";
            body.appendChild(empty);
        } else {
            dayEvents.forEach(event => {
                const card = document.createElement("div");
                card.className = "calendar-booking-card";

                if (event.venue_color) {
                    card.style.borderLeftColor = event.venue_color;
                }

                card.innerHTML = `
                    <div class="calendar-booking-title">${event.title}</div>
                    <div class="calendar-booking-time">
                        ${formatTime(event.start)} - ${formatTime(event.end)}
                    </div>
                    <div class="calendar-booking-meta">
                        ${event.contact_name ?? ""}
                    </div>
                `;

                body.appendChild(card);
            });
        }

        dayColumn.appendChild(header);
        dayColumn.appendChild(body);
        grid.appendChild(dayColumn);
    }
}

document.getElementById("prev-week").addEventListener("click", () => {
    currentDate.setDate(currentDate.getDate() - 7);
    loadCalendar();
});

document.getElementById("next-week").addEventListener("click", () => {
    currentDate.setDate(currentDate.getDate() + 7);
    loadCalendar();
});

loadCalendar();