import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const html = fs.readFileSync(new URL('../docs/index.html', import.meta.url), 'utf8');
const scriptMatch = html.match(/<script>([\s\S]*?)fetch\('bandsheet-data\.json'\)/);
assert.ok(scriptMatch, 'Could not find inline bandsheet script before data fetch');

const context = {
  console,
  document: {
    getElementById() {
      return { innerHTML: '', appendChild() {} };
    },
    createElement() {
      return {
        className: '',
        textContent: '',
        appendChild() {},
        setAttribute() {},
      };
    },
  },
};

vm.createContext(context);
vm.runInContext(scriptMatch[1], context);

assert.equal(typeof context.buildAvailabilityMonths, 'function');

const months = context.buildAvailabilityMonths([
  '- FRI July 24',
  '- SAT July 25',
  '- SUN August 2',
]);

assert.equal(JSON.stringify(months.map((month) => month.label)), JSON.stringify(['July', 'August']));
assert.equal(JSON.stringify(Array.from(months[0].openDays)), JSON.stringify([24, 25]));
assert.equal(months[0].firstWeekday, 3);
assert.equal(months[0].daysInMonth, 31);
assert.equal(JSON.stringify(Array.from(months[1].openDays)), JSON.stringify([2]));
