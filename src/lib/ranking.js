// Similarity ranking, shared by routes/+page.svelte and workers/rankWorker.js
// (and by the offline test script in the rebuttal workspace).
//
// Follows paper App. C.2: every ranked feature is put in [0, 1] before weighting, so no
// feature's measurement unit can dominate the ranking.
//   - s   (source)   : categorical, user = 1, AI = 0 (a mismatch costs 1).
//   - p   (progress) : per-block progress delta, robustly scaled with the dataset median/IQR.
//   - sem (semantic) : per-block semantic change, robustly scaled with the dataset median/IQR.
//   - tr  (trend)    : least-squares slope of semantic change across the window's blocks,
//                      robustly scaled with the median/IQR of all same-length windows.
// Time is NOT ranked: there is no justified way to put durations in [0, 1]. It stays a
// hard constraint in findSegments() (+page.svelte).
//
// Distance = sum over features of weight * (mean squared difference over the feature's
// elements). With all weights = 1, each feature contributes a value in [0, 1].
//
// Units of the inputs:
//   candidate blocks (segment_results data): start/end_progress in 0-1.
//   reference blocks (the user's selection): progress in percent (0-100);
//     bar chart sends startProgress/endProgress, line chart sends start_progress/end_progress.

export const RANKED_FEATURES = ["s", "p", "sem", "tr"];

// x' = clamp(0.5 + (x - median) / (IQR_SPAN * IQR), 0, 1):
// the median maps to 0.5 and median +/- 2 IQR map to 1 / 0; values further out are clipped.
const IQR_SPAN = 4;

const clamp01 = (x) => Math.min(1, Math.max(0, x));

// ---------- statistics ----------

// Linear-interpolated quantile of an already sorted numeric array.
function quantileSorted(sorted, q) {
  if (sorted.length === 0) return 0;
  const pos = (sorted.length - 1) * q;
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

function medianIqr(values) {
  const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
  const q1 = quantileSorted(sorted, 0.25);
  const q3 = quantileSorted(sorted, 0.75);
  return { median: quantileSorted(sorted, 0.5), iqr: q3 - q1 };
}

// Robust scaling into [0, 1]. If the IQR is 0 (no spread), every value maps to 0.5,
// so the feature cannot separate candidates and adds nothing to the distance.
export function robustScale(x, stat) {
  const v = Number(x);
  if (!Number.isFinite(v) || !stat || !(stat.iqr > 0)) return 0.5;
  return clamp01(0.5 + (v - stat.median) / (IQR_SPAN * stat.iqr));
}

// Least-squares slope of values against their index (0, 1, 2, ...). 0 for < 2 values.
export function slope(values) {
  const ys = values.map(Number);
  const n = ys.length;
  if (n < 2 || ys.some((y) => !Number.isFinite(y))) return 0;
  const meanX = (n - 1) / 2;
  const meanY = ys.reduce((a, b) => a + b, 0) / n;
  let num = 0;
  let den = 0;
  for (let i = 0; i < n; i++) {
    num += (i - meanX) * (ys[i] - meanY);
    den += (i - meanX) ** 2;
  }
  return num / den;
}

// A session's block array, whatever shape the stored JSON has (same rule as +page.svelte).
export function blocksOf(data) {
  if (Array.isArray(data)) return data;
  return data?.chartData || data?.totalSimilarityData || [];
}

// Dataset statistics used for robust scaling.
// sessions: array of block arrays (one per session, segment_results format).
// windowSize: number of blocks in the searched pattern (trend slopes depend on it).
export function computeRankingStats(sessions, windowSize) {
  const progress = [];
  const semantic = [];
  const slopes = [];
  for (const blocks of sessions) {
    for (const b of blocks) {
      progress.push(b.end_progress - b.start_progress);
      semantic.push(Number(b.residual_vector_norm));
    }
    for (let i = 0; i + windowSize <= blocks.length; i++) {
      slopes.push(
        slope(blocks.slice(i, i + windowSize).map((b) => b.residual_vector_norm)),
      );
    }
  }
  return { p: medianIqr(progress), sem: medianIqr(semantic), tr: medianIqr(slopes) };
}

// ---------- distance ----------

// Mean squared difference of two [0, 1] arrays. Positions present in only one array,
// or with a non-numeric value, count as the maximum difference (1).
export function featureDistance(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b)) return 0;
  const n = Math.max(a.length, b.length);
  if (n === 0) return 0;
  let sum = 0;
  for (let i = 0; i < n; i++) {
    if (i >= a.length || i >= b.length) {
      sum += 1;
      continue;
    }
    const d = Number(a[i]) - Number(b[i]);
    sum += Number.isFinite(d) ? d * d : 1;
  }
  return sum / n;
}

// Only RANKED_FEATURES count; other keys on the vector (id, segmentId) are ignored.
export function rankingDistance(item, ref, weights = {}) {
  let score = 0;
  for (const key of RANKED_FEATURES) {
    if (!(key in item) || !(key in ref)) continue;
    score += (weights[key] ?? 1) * featureDistance(item[key], ref[key]);
  }
  return score;
}

// Returns [[segmentId, score], ...] sorted by ascending distance (most similar first).
export function rankVectors(patternVectors, currentVector, weights = {}) {
  const result = patternVectors.map((item) => [
    item.segmentId,
    rankingDistance(item, currentVector, weights),
  ]);
  result.sort((a, b) => a[1] - b[1]);
  return result;
}

// ---------- vectors ----------
// checks: the same object as in +page.svelte, e.g. checks.source = [isOn, expectedSources].
// stats:  output of computeRankingStats() for the searched dataset.

// Vector for a candidate window (segment_results blocks, progress in 0-1).
export function buildCandidateVector(segment, checks, stats) {
  const vector = {};
  if (checks.source[0]) {
    vector.s = segment.map((b) => (b.source?.toLowerCase() === "user" ? 1 : 0));
  }
  if (checks.progress[0]) {
    vector.p = segment.map((b) =>
      robustScale(b.end_progress - b.start_progress, stats.p),
    );
  }
  if (checks.semantic[0]) {
    vector.sem = segment.map((b) => robustScale(b.residual_vector_norm, stats.sem));
  }
  if (checks.trend[0]) {
    vector.tr = [robustScale(slope(segment.map((b) => b.residual_vector_norm)), stats.tr)];
  }
  return vector;
}

// Vector for the user's selected reference blocks (progress in percent, see top).
export function buildReferenceVector(items, checks, stats) {
  const vector = {};
  if (checks.source[0]) {
    // Expected sources come from the selection (checks.source[1]), as before.
    vector.s = items.map((_, i) => (checks.source[1][i] === "user" ? 1 : 0));
  }
  if (checks.progress[0]) {
    vector.p = items.map((b) => {
      const start = b.startProgress ?? b.start_progress;
      const end = b.endProgress ?? b.end_progress;
      return robustScale((end - start) / 100, stats.p);
    });
  }
  if (checks.semantic[0]) {
    vector.sem = items.map((b) => robustScale(b.residual_vector_norm, stats.sem));
  }
  if (checks.trend[0]) {
    vector.tr = [robustScale(slope(items.map((b) => b.residual_vector_norm)), stats.tr)];
  }
  return vector;
}
