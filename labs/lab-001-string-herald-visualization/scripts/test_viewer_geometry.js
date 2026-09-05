#!/usr/bin/env node
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const viewerPath = path.resolve(__dirname, "../figures/string-herald-sample.html");
const html = fs.readFileSync(viewerPath, "utf8");
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
assert(scriptMatch, "viewer must contain one inline script");
const script = scriptMatch[1];
new Function(script);

const geometryMatch = script.match(/function segmentsCross[\s\S]*?(?=\n\s+function symmetricDifference)/);
assert(geometryMatch, "pure geometry block must remain extractable");
const geometry = new Function(`${geometryMatch[0]}; return {squareGraph, honeycombGraph};`)();
const displayUtilityMatch = script.match(/function symmetricDifference[\s\S]*?(?=\n\s+async function requestStageOne)/);
assert(displayUtilityMatch, "pure display utility block must remain extractable");
const displayUtilities = new Function(`${displayUtilityMatch[0]}; return {edgeDegree};`)();
const span = (points, axis) => Math.max(...points.map(point => point[axis])) - Math.min(...points.map(point => point[axis]));
const assertRotatedCut = graph => {
  const smoothPoints = graph.boundary.smooth.flat();
  assert(graph.logicalLine[0].x < Math.min(...smoothPoints.map(point => point.x)));
  assert(graph.logicalLine.at(-1).x > Math.max(...smoothPoints.map(point => point.x)));
  assert(span(graph.logicalLine, "y") < 1e-6, "logical cut must be horizontal after rotation");
};

for (const size of [3, 5, 12]) {
  const square = geometry.squareGraph(size);
  assert.equal(square.boundaryEdgeCounts.left, size);
  assert.equal(square.boundaryEdgeCounts.right, size);
  assert.equal(square.boundaryEdgeIndices.size, 2 * size);
  assert.equal(square.logicalEdgeIndices.size, size);
  assertRotatedCut(square);

  const honeycomb = geometry.honeycombGraph(size);
  assert(honeycomb.boundaryEdgeCounts.left > 0);
  assert(honeycomb.boundaryEdgeCounts.right > 0);
  assert.equal(
    honeycomb.boundaryEdgeIndices.size,
    honeycomb.boundaryEdgeCounts.left + honeycomb.boundaryEdgeCounts.right,
  );
  assert.equal(honeycomb.logicalEdgeIndices.size, size + 1);
  assert(honeycomb.boundary.smooth.every(chain => chain.length > 2));
  assert(honeycomb.boundary.smooth.every(chain => new Set(chain.map(point => point.x.toFixed(4))).size > 1));
  assertRotatedCut(honeycomb);
  assert(span(honeycomb.vertices, "x") > span(honeycomb.vertices, "y"), "rotated honeycomb must be wider than tall");
}

// Exact browser configuration used by the Python decoder regression:
// square L=9, p=0.20, q=1, p_m=p_h=0, seed=1.
const seededSquare = geometry.squareGraph(9);
let seededState = 1;
const seededRandom = () => ((seededState = (1664525 * seededState + 1013904223) >>> 0) / 4294967296);
const seededErrors = new Set();
seededSquare.edges.forEach((_, edge) => { if (seededRandom() < 0.20) seededErrors.add(edge); });
const seededDegree = displayUtilities.edgeDegree(seededSquare.vertices.length, seededSquare.edges, seededErrors);
const seededHeralds = new Set(
  seededSquare.vertices
    .filter(vertex => vertex.detector && seededDegree[vertex.id] >= 2)
    .map(vertex => vertex.id),
);
assert(seededHeralds.size > 0, "seed-1 sample must expose herald input to the Lab decoder");

assert(script.includes("/api/labs/lab-001-string-herald-visualization/predecode"));
assert(script.includes("result.algorithm_source!=='scripts/local_decoder.py'"));
assert(html.includes("result=stage-one-decoder"));
for (const forbidden of [
  "function shortestPath",
  "parallelHeraldPaths",
  "addHeraldPaths",
  "syndromeNeighbors",
]) {
  assert(!script.includes(forbidden), `viewer must not duplicate Python decoder logic: ${forbidden}`);
}

assert(html.includes('id="size-input" type="range" min="3" max="12" step="1" value="9"'));
assert(!html.includes("rough · open"));
assert(!/<text[^>]*>smooth<\/text>/.test(html));

for (const id of [
  "view-name",
  "error-density",
  "syndrome-density",
  "herald-density",
  "logical-result",
]) {
  assert(html.includes(`id="${id}"`), `missing live statistic ${id}`);
}

console.log("viewer geometry and statistics contract: OK");
