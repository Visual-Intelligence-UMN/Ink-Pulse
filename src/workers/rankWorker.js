self.onmessage = function (e) {
  const { patternVectors, currentVector, weights } = e.data;

  function l2(a, b) {
    if (!a || !b || a.length !== b.length) return Infinity;
    let sum = 0;
    for (let i = 0; i < a.length; i++) {
      const d = a[i] - b[i];
      sum += d * d;
    }
    return sum;
  }

  let result = [];

  for (const item of patternVectors) {
    let score = 0;
    for (const key in weights) {
      score += weights[key] * l2(item[key], currentVector[key]);
    }
    result.push([item.segmentId, score]);
  }

  self.postMessage(result);
};
