#!/usr/bin/env node
"use strict";

// Test the actual helper declarations in source AND generated distribution.
// DOM rendering/CSS/sanitization are covered separately by browser_icon_strokes.py.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");

function loadDefaults(relative) {
  const text = fs.readFileSync(path.join(root, relative), "utf8");
  const attributes = text.match(/  const LUCIDE_ATTRIBUTES = Object\.freeze\(\{[\s\S]*?\n  \}\);/);
  const start = text.indexOf("  function defaultIconStrokeWidth(svg) {");
  const end = text.indexOf("  function createLucideIcon(", start);
  assert.ok(attributes && start >= 0 && end > start, `${relative}: expected helpers missing`);
  const context = vm.createContext({});
  vm.runInContext(
    `${attributes[0]}\n${text.slice(start, end)}\nglobalThis.applyDefaults = addLucideDefaults;`,
    context,
    { timeout: 1000, filename: relative }
  );
  return context.applyDefaults;
}

function fakeSvg(initial) {
  const attributes = new Map(Object.entries(initial));
  return {
    getAttribute: (key) => attributes.has(key) ? attributes.get(key) : null,
    hasAttribute: (key) => attributes.has(key),
    setAttribute: (key, value) => attributes.set(key, String(value)),
    attributes,
  };
}

const defaults = [
  [undefined, "2"],
  ["0 0 24 24", "2"],
  ["0 0 48 48", "4"],
  ["  0  0  48  48  ", "4"],
  ["0,0,48,48", "4"],
  ["0, 0, 48, 48", "4"],
  ["0\t0\n48\t48", "4"],
  ["0.0 0.0 48.0 48.0", "4"],
  ["+0 -0 4.8e1 48", "4"],
  ["-24 -24 48 48", "4"],
  ["0 0 48 24", "2"],
  ["0 0 24 48", "2"],
  ["0 0 96 96", "2"],
  ["0 0 32 32", "2"],
  ["", "2"],
  ["0 0 48", "2"],
  ["0 0 48 48 1", "2"],
  ["0 0 NaN 48", "2"],
  ["0 0 Infinity 48", "2"],
  ["0 0 -48 48", "2"],
  ["0 0 0x30 0x30", "2"],
  ["no viewBox", "2"],
];
let cases = 0;
for (const relative of ["src/marinos.js", "dist/marinos.js"]) {
  const applyDefaults = loadDefaults(relative);
  for (const [viewBox, expected] of defaults) {
    const initial = { "data-app-owned": "keep" };
    if (viewBox !== undefined) initial.viewBox = viewBox;
    const svg = fakeSvg(initial);
    assert.equal(applyDefaults(svg), svg);
    assert.equal(svg.getAttribute("stroke-width"), expected, `${relative}: ${JSON.stringify(viewBox)}`);
    assert.equal(svg.getAttribute("viewBox"), viewBox === undefined ? "0 0 24 24" : viewBox);
    assert.equal(svg.getAttribute("data-app-owned"), "keep");
    assert.equal(svg.getAttribute("fill"), "none");
    assert.equal(svg.getAttribute("stroke"), "currentColor");
    assert.equal(svg.getAttribute("aria-hidden"), "true");
    assert.equal(svg.getAttribute("focusable"), "false");
    const once = Array.from(svg.attributes);
    applyDefaults(svg);
    assert.deepEqual(Array.from(svg.attributes), once, `${relative}: defaults are not idempotent`);
    cases += 1;
  }
  for (const viewBox of ["0 0 24 24", "0 0 48 48"]) {
    for (const width of ["0", "1.5", "2", "4", "6"]) {
      const svg = fakeSvg({ viewBox, "stroke-width": width, stroke: "red", fill: "blue" });
      applyDefaults(svg);
      assert.equal(svg.getAttribute("stroke-width"), width, `${relative}: explicit width was overwritten`);
      assert.equal(svg.getAttribute("viewBox"), viewBox);
      assert.equal(svg.getAttribute("stroke"), "red");
      assert.equal(svg.getAttribute("fill"), "blue");
      cases += 1;
    }
  }
}
console.log(`icon_stroke_defaults.js: PASS (${cases} source/distribution cases)`);
