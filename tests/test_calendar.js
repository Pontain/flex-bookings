// Optional DOM-level checks: node tests/test_calendar.js (no npm dependencies).
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const js = path.join(__dirname, '../app/static/js');
for (const zone of ['UTC','Europe/Stockholm','America/Los_Angeles']) {
    process.env.TZ = zone;
    for (const name of ['calendar','dashboard']) {
        const elements = {};
        function element() {
            return {children:[], classList:{add(){},remove(){}}, style:{}, dataset:{},
                appendChild(child){this.children.push(child)}, addEventListener(){},
                set textContent(v){this.text=String(v)},
                get innerHTML(){return this.html ?? (this.text ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')},
                set innerHTML(v){this.html=v;this.children=[]}};
        }
        elements[name==='calendar'?'calendar-grid':'dashboard-calendar']=element();
        const context = vm.createContext({Intl,Date,console,document:{
            getElementById(id){return elements[id] ?? null},createElement:element,addEventListener(){},querySelectorAll(){return []}
        },setTimeout(){}});
        vm.runInContext(fs.readFileSync(path.join(js,'time.js'),'utf8')+'\n'+fs.readFileSync(path.join(js,name+'.js'),'utf8'),context);
        assert.equal(vm.runInContext('formatTime("2026-11-01T09:00:00Z")',context),'10:00');
        assert.equal(vm.runInContext('calendarBoundary(swedishClockDate("2026-06-01T22:00:00Z"))',context),'2026-06-02T00:00:00');
        vm.runInContext(`const attack = '<img src=x onerror="alert(1)">';
            const events = [{id:1,title:attack,contact_name:attack,start:'2026-11-01T09:00:00Z',end:'2026-11-01T10:00:00Z'}];
            ${name==='calendar'?'renderCalendar(new Date("2026-11-01T00:00:00Z"), events)':'renderDashboardCalendar("2026-11-01", events)'};`,context);
        const all=[];function collect(e){all.push(e.innerHTML);e.children.forEach(collect)}
        collect(elements[name==='calendar'?'calendar-grid':'dashboard-calendar']);
        const card=all.find(x=>x.includes('onerror'));
        assert(card && card.includes('&lt;img') && !card.includes('<img'),`${name} unsafe interpolation`);
    }
}
console.log('Calendar DOM tests passed in 3 time zones, both views.');
