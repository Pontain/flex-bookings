// Calendar dates are UTC carriers of Swedish clock fields, not actual instants.
// This keeps calendar days stable even when the browser uses another time zone.
function swedishClockDate(value = new Date()) {
    const parts = Object.fromEntries(new Intl.DateTimeFormat("sv-SE", {
        timeZone: "Europe/Stockholm", year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23"
    }).formatToParts(new Date(value)).map(part => [part.type, part.value]));
    return new Date(Date.UTC(+parts.year, +parts.month - 1, +parts.day,
        +parts.hour, +parts.minute, +parts.second));
}
function calendarBoundary(date) {
    // No offset: the backend interprets these calendar boundaries in Stockholm.
    return date.toISOString().slice(0, 19);
}
