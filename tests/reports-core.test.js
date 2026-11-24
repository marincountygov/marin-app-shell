const test = require('node:test');
const assert = require('node:assert');
const R = require('../src/reports-core.js');
const sample = () => R.create({ title: 'Report <report>', prepared: '2026-11-18', filters: 'Showing: all', sources: [{ label: 'Book', url: 'https://example.org/b.pdf' }, { label: 'Bad', url: 'javascript:alert(1)' }],
  sections: [{ type: 'table', head: ['Area', 'FY 2026-27'], rows: [['Safety', '$1'], ['A|B', '$2']], values: [['Safety', 1], ['A|B', 2]] }] }).report;

test('a report is escaped, dated, and keeps only safe links', () => {
  const r = sample();
  const html = R.renderHtml(r);
  assert.match(html, /<h2>Report &lt;report&gt;<\/h2><p>Prepared November 18, 2026<\/p>/);
  assert.match(html, /<a href="https:\/\/example.org\/b.pdf">Book<\/a>/);
  assert.ok(!html.includes('javascript:'));
  assert.ok(!html.includes('<report>'));
});

test('markdown escapes a backslash before a pipe, so a value cannot split its table row', () => {
  const report = { title: 'T', filters: '', sections: [{ title: '', head: ['Name', 'Value'], rows: [['C:\\data', 1], ['a\\|b', 2], ['ends with\\', 3]] }], sources: [] };
  const md = R.toMarkdown(report);
  assert.ok(md.includes('| C:\\\\data | 1 |'), md);
  assert.ok(md.includes('| a\\\\\\|b | 2 |'), md);
  assert.ok(md.includes('| ends with\\\\ | 3 |'), md);
  // every body row has exactly the two cells: an unescaped pipe would make three
  for (const row of md.split('\n').filter((l) => /^\| (C:|a|ends)/.test(l))) assert.strictEqual(row.replace(/\\./g, '').split('|').length - 2, 2, row);
});

test('text, markdown, standalone page and csv come from the same report', () => {
  const r = sample();
  assert.match(R.toText(r), /^Report <report>\nPrepared November 18, 2026\nShowing: all\n\nArea \| FY 2026-27\nSafety \| \$1/);
  assert.match(R.toMarkdown(r), /\| A\\\|B \| \$2 \|/);
  assert.match(R.standaloneHtml(r), /^<!doctype html>.*<h1>Report &lt;report&gt;<\/h1>/);
  assert.deepStrictEqual(R.csvRows(r)[1], ['Safety', 1]);
});

test('a report file reads back the same, and a wrong file is refused', () => {
  const r = sample();
  const back = R.parseJson(R.toJson(r));
  assert.deepStrictEqual(back.report, r);
  assert.ok(R.parseJson('{"schema":"9"}').errors.length);
  assert.ok(R.parseJson('not json').errors.length);
  assert.ok(R.parseJson('{"schema":"1.0","sections":[]}').errors.length);
});

test('fields left empty are not drawn', () => {
  const r = R.create({ title: 'T', sections: [{ type: 'table', head: ['A'], rows: [['x']] }] }).report;
  assert.doesNotMatch(R.renderHtml(r), /Prepared|Source/);
});

test('several tables make one csv, each under its title', () => {
  const r = R.create({ title: 'T', sections: [{ type: 'table', title: 'A', head: ['x'], rows: [['1']] }, { type: 'table', title: 'B', head: ['y'], rows: [['2']] }] }).report;
  assert.deepStrictEqual(R.csvRows(r), [['A'], ['x'], ['1'], [], ['B'], ['y'], ['2']]);
});

const PNG = 'data:image/png;base64,iVBORw0KGgo=';
const withChart = (image) => R.create({ title: 'T', sections: [{ type: 'table', title: 'S', head: ['A', 'B'], rows: [['x', '1']],
  chart: { kind: 'columns', title: 'S chart', summary: 'x is the largest.', labels: ['x'], series: [{ name: 'B', values: [1] }], image, width: 900, height: 400 } }] }).report;

test('a chart is drawn from its picture and said in words for text', () => {
  const r = withChart(PNG);
  assert.match(R.renderHtml(r), /<figure[^>]*><img src="data:image\/png;base64,iVBORw0KGgo=" alt="S chart. x is the largest." width="900" height="400"/);
  assert.match(R.toText(r), /Chart: x is the largest\./);
  assert.match(R.toMarkdown(r), /Chart: x is the largest\./);
  assert.strictEqual(R.parseJson(R.toJson(r)).report.sections[0].chart.image, PNG);
});

test('a chart picture that is not a PNG data address is dropped, and the sentence stays', () => {
  const r = withChart('javascript:alert(1)');
  assert.strictEqual(r.sections[0].chart.image, '');
  assert.ok(!R.renderHtml(r).includes('<img'));
  assert.match(R.renderHtml(r), /<p>x is the largest\.<\/p>/);
});

test('a figure with a margin and a bound keeps both in the csv, in columns of their own', () => {
  const r = R.create({ title: 'T', sections: [{ type: 'table', head: ['Place', 'Income', 'Rent'], rows: [['A', '$149,091 \u00b1 $4,474', '$2,668'], ['B', '$250,000 or more', '$3,000']],
    values: [['A', { value: 149091, margin: 4474 }, 2668], ['B', { min: 250000 }, 3000]] }] }).report;
  assert.deepStrictEqual(R.csvRows(r), [
    ['Place', 'Income', 'Income margin of error', 'Income lower bound', 'Rent'],
    ['A', 149091, 4474, '', 2668],
    ['B', '', '', 250000, 3000],
  ]);
});

test('a column of plain numbers has no extra columns, and a bad cell object becomes empty text', () => {
  const r = R.create({ title: 'T', sections: [{ type: 'table', head: ['A', 'B'], rows: [['x', '1']], values: [['x', { value: 'NaN', margin: Infinity }]] }] }).report;
  assert.deepStrictEqual(r.sections[0].values, [['x', '']]);
  assert.deepStrictEqual(R.csvRows(r), [['A', 'B'], ['x', '']]);
});

test('a margin survives saving and opening the report file', () => {
  const r = R.create({ title: 'T', sections: [{ type: 'table', head: ['A'], rows: [['1']], values: [[{ value: 1, margin: 0.5 }]] }] }).report;
  assert.deepStrictEqual(R.parseJson(R.toJson(r)).report.sections[0].values, [[{ value: 1, margin: 0.5 }]]);
});
