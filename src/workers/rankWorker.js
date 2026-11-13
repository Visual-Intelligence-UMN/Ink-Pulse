// Ranks one chunk of candidate vectors off the main thread (used for > 100 candidates).
// Uses the same distance as the main thread (src/lib/ranking.js), so the order does not
// depend on how many candidates there are. Vectors arrive already scaled to [0, 1].
import { rankingDistance } from "../lib/ranking.js";

self.onmessage = function (e) {
  const { patternVectors, currentVector, weights } = e.data;
  const result = patternVectors.map((item) => [
    item.segmentId,
    rankingDistance(item, currentVector, weights),
  ]);
  self.postMessage(result);
};
