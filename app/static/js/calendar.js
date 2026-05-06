let currentDate = new Date();

/* =========================
   Gemensam modal-funktionalitet
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

/* =========================
   Veckovy-funktioner
========================= */

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
    const weekLabel = document.getElementById("week-label");
    const calendarGrid = document.getElementById("calendar-grid");

    if (!weekLabel || !calendarGrid) {
        return;
    }

    const weekStart = startOfWeek(currentDate);
    const weekEnd = endOfWeek(currentDate);

    weekLabel.textContent = formatWeekLabel(weekStart);

    try {
        const response = await fetch(
            `/calendar/events?start=${encodeURIComponent(weekStart.toISOString())}&end=${encodeURIComponent(weekEnd.toISOString())}`
        );

        if (!response.ok) {
            calendarGrid.innerHTML = "<p>Kunde inte ladda kalendern.</p>";
            return;
        }

        const events = await response.json();
        renderCalendar(weekStart, events);
    } catch (error) {
        calendarGrid.innerHTML = "<p>Ett fel uppstod när kalendern skulle laddas.</p>";
        console.error(error);
    }
}

function formatEventTimeForDay(event, dayDate) {
    const eventStart = new Date(event.start);
    const eventEnd = new Date(event.end);

    const dayStart = new Date(dayDate);
    dayStart.setHours(0, 0, 0, 0);

    const dayEnd = new Date(dayDate);
    dayEnd.setDate(dayEnd.getDate() + 1);
    dayEnd.setHours(0, 0, 0, 0);

    const startsToday = eventStart >= dayStart && eventStart < dayEnd;
    const endsToday = eventEnd > dayStart && eventEnd <= dayEnd;

    if (startsToday && endsToday) {
        return `${formatTime(event.start)} - ${formatTime(event.end)}`;
    }

    if (startsToday) {
        return `${formatTime(event.start)} - fortsätter`;
    }

    if (endsToday) {
        return `fortsätter - ${formatTime(event.end)}`;
    }

    return "Heldag / fortsätter";
}


function renderCalendar(weekStart, events) {
    const grid = document.getElementById("calendar-grid");
    if (!grid) {
        return;
    }

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

        const bodyWrapper = document.createElement("div");
        bodyWrapper.className = "calendar-day-body-wrapper";

        const scrollUp = document.createElement("button");
        scrollUp.type = "button";
        scrollUp.className = "scroll-btn scroll-up";
        scrollUp.textContent = "▲";

        const body = document.createElement("div");
        body.className = "calendar-day-body";

        const scrollDown = document.createElement("button");
        scrollDown.type = "button";
        scrollDown.className = "scroll-btn scroll-down";
        scrollDown.textContent = "▼";

        const dayStart = new Date(dayDate);
        dayStart.setHours(0, 0, 0, 0);

        const dayEnd = new Date(dayDate);
        dayEnd.setDate(dayEnd.getDate() + 1);
        dayEnd.setHours(0, 0, 0, 0);

        const dayEvents = events
            .filter(event => {
                const eventStart = new Date(event.start);
                const eventEnd = new Date(event.end);

                return eventStart < dayEnd && eventEnd > dayStart;
            })
            .sort((a, b) => new Date(a.start) - new Date(b.start));

        if (dayEvents.length === 0) {
            const empty = document.createElement("div");
            empty.className = "calendar-empty";
            empty.textContent = "Inga bokningar";
            body.appendChild(empty);
        } else {
            dayEvents.forEach(event => {
                const card = document.createElement("button");
                card.type = "button";
                card.className = "calendar-booking-card";
                card.onclick = () => {
                console.log("Klick på bokning:", event);
                openBookingModal(event.id);
                };

                if (event.venue_color) {
                    card.style.borderLeftColor = event.venue_color;
                }

                card.innerHTML = `
                    <div class="calendar-booking-title">${event.title}</div>
                    <div class="calendar-booking-time">
                        ${formatEventTimeForDay(event, dayDate)}
                    </div>
                    <div class="calendar-booking-meta">
                        ${event.contact_name ?? ""}
                    </div>
                `;

                body.appendChild(card);
            });
        }

        bodyWrapper.appendChild(scrollUp);
        bodyWrapper.appendChild(body);
        bodyWrapper.appendChild(scrollDown);

        scrollUp.addEventListener("click", () => {
            body.scrollBy({ top: -80, behavior: "smooth" });
        });

        scrollDown.addEventListener("click", () => {
            body.scrollBy({ top: 80, behavior: "smooth" });
        });

        const updateScrollButtons = () => {
            scrollUp.style.display = body.scrollTop > 0 ? "block" : "none";
            scrollDown.style.display =
                body.scrollTop + body.clientHeight < body.scrollHeight
                    ? "block"
                    : "none";
        };

        body.addEventListener("scroll", updateScrollButtons);

        setTimeout(updateScrollButtons, 0);

        dayColumn.appendChild(header);
        dayColumn.appendChild(bodyWrapper);
        grid.appendChild(dayColumn);
    }
}

/* =========================
   Månadsvy-funktioner
========================= */

const monthLabel = document.getElementById("month-label");
const prevMonthBtn = document.getElementById("prev-month");
const nextMonthBtn = document.getElementById("next-month");

if (monthLabel && prevMonthBtn && nextMonthBtn) {
    const currentYear = parseInt(monthLabel.dataset.year, 10);
    const currentMonth = parseInt(monthLabel.dataset.month, 10);

    function goToMonth(year, month) {
        window.location.href = `/calendar/month?year=${year}&month=${month}`;
    }

    prevMonthBtn.addEventListener("click", () => {
        let year = currentYear;
        let month = currentMonth - 1;

        if (month < 1) {
            month = 12;
            year -= 1;
        }

        goToMonth(year, month);
    });

    nextMonthBtn.addEventListener("click", () => {
        let year = currentYear;
        let month = currentMonth + 1;

        if (month > 12) {
            month = 1;
            year += 1;
        }

        goToMonth(year, month);
    });
}


/* =========================
   Init
========================= */

document.addEventListener("DOMContentLoaded", () => {
    const prevWeekBtn = document.getElementById("prev-week");
    const nextWeekBtn = document.getElementById("next-week");
    const calendarGrid = document.getElementById("calendar-grid");

    document.querySelectorAll("[data-venue-color]").forEach((element) => {
        element.style.borderLeft = `4px solid ${element.dataset.venueColor}`;
    });

    if (prevWeekBtn) {
        prevWeekBtn.addEventListener("click", () => {
            currentDate.setDate(currentDate.getDate() - 7);
            loadCalendar();
        });
    }

    if (nextWeekBtn) {
        nextWeekBtn.addEventListener("click", () => {
            currentDate.setDate(currentDate.getDate() + 7);
            loadCalendar();
        });
    }

    if (calendarGrid) {
        loadCalendar();
    }
});

