import test from "node:test";
import assert from "node:assert/strict";
import { initialWeights, updateWeights, rerankCandidates } from "./ranking.js";

test("C.3 mixes separation with old weights and normalizes only active features", () => {
  const reference = { p: [0], sem: [0] };
  const original = initialWeights(reference);
  const next = updateWeights(original, reference, [{ p: [0.2], sem: [0.8] }]);
  const rawP = 0.75 * 0.5 + 0.25 * (0.04 + 1e-6);
  const rawSem = 0.75 * 0.5 + 0.25 * (0.64 + 1e-6);
  assert.ok(Math.abs(next.p - rawP / (rawP + rawSem)) < 1e-12);
  assert.ok(Math.abs(next.sem - rawSem / (rawP + rawSem)) < 1e-12);
  assert.ok(next.sem > next.p);
  assert.equal(next.s, 0);
  assert.equal(next.t, 0);
  assert.equal(next.tr, 0);
  assert.equal(original.p, 0.5);
});

test("C.3 uses all rejections' median and includes the reference in kept examples", () => {
  const reference = { p: [0], sem: [0] };
  const weights = initialWeights(reference);
  const negatives = [
    { p: [0.1], sem: [0.1] },
    { p: [0.2], sem: [0.8] },
    { p: [1], sem: [0.9] },
  ];
  const next = updateWeights(weights, reference, negatives, [{ p: [0.8], sem: [0.2] }]);
  // median negative p = .04; median kept p = (.64 + 0) / 2 = .32.
  // median negative sem = .64; median kept sem = (.04 + 0) / 2 = .02.
  const rawP = 0.375 + 0.25e-6;
  const rawSem = 0.375 + 0.25 * (0.62 + 1e-6);
  assert.ok(Math.abs(next.sem - rawSem / (rawP + rawSem)) < 1e-12);
  assert.deepEqual(updateWeights(weights, reference, []), weights);
  assert.deepEqual(updateWeights(initialWeights({}), {}, [{}]), initialWeights({}));
});

test("successive deletion feedback updates weights while preserving each prefix", () => {
  const reference = { p: [0], sem: [0] };
  const vectors = [
    { segmentId: "kept-in-place", p: [1], sem: [1] },
    { segmentId: "reject", p: [0], sem: [1] },
    { segmentId: "progress-match", p: [0], sem: [0.8] },
    { segmentId: "semantic-match", p: [0.8], sem: [0] },
    { segmentId: "other", p: [0.7], sem: [0.7] },
  ];
  const next = updateWeights(initialWeights(reference), reference, [vectors[1]]);
  const ids = vectors.map(({ segmentId }) => segmentId);
  const ordered = rerankCandidates(ids, "reject", vectors, reference, next);
  assert.deepEqual(ordered, ["kept-in-place", "semantic-match", "progress-match", "other"]);
  const updated = updateWeights(next, reference, [vectors[1], vectors[2]]);
  assert.ok(Math.abs(updated.p + updated.sem - 1) < 1e-12);
  assert.deepEqual(rerankCandidates(ordered, "progress-match", vectors, reference, updated,
    new Set(["reject"])), ["kept-in-place", "semantic-match", "other"]);
});

test("initial weights split only between selected features", () => {
  assert.deepEqual(initialWeights({ p: [0.2], sem: [0.8] }), {
    t: 0, s: 0, p: 0.5, sem: 0.5, tr: 0,
  });
  assert.deepEqual(initialWeights({}), { t: 0, s: 0, p: 0, sem: 0, tr: 0 });
});

test("deleting the sixth result preserves the first five and reranks the full tail", () => {
  const ids = ["a", "b", "c", "d", "e", "rejected", "g", "h", "i"];
  const vectors = ids.map((segmentId, index) => ({ segmentId, p: [index / 10], sem: [1 - index / 10] }));
  const result = rerankCandidates(ids, "rejected", vectors, { p: [0], sem: [0] }, {
    s: 0, p: 0, sem: 1, tr: 0,
  });
  assert.deepEqual(result, ["a", "b", "c", "d", "e", "i", "h", "g"]);
  assert.deepEqual(ids, ["a", "b", "c", "d", "e", "rejected", "g", "h", "i"]);
});

test("repeated deletions exclude old rejections and keep ties stable", () => {
  const vectors = ["a", "b", "c", "d"].map((segmentId) => ({ segmentId, p: [0.5] }));
  assert.deepEqual(rerankCandidates(["a", "b", "c", "d"], "b", vectors, { p: [0] },
    { p: 1 }, new Set(["c"])), ["a", "d"]);
  assert.deepEqual(rerankCandidates(["a", "b", "c", "d"], "a", vectors, { p: [0] },
    { p: 1 }), ["b", "c", "d"]);
});
