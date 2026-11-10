/* Mirrors aire_abierto.livability.scoring.combine.
   The mart already stores each piece on the fixed 0–100 scale.
   This file only drops empty pieces and rescales the weights. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
  root.LivabilityScore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const KEYS = ["air", "safety", "perception", "rent"];

  function combine(components, weights, minimum) {
    const floor = minimum === undefined ? 2 : minimum;
    const available = [];
    KEYS.forEach(function (key) {
      const weight = Number(weights[key] || 0);
      const value = components[key];
      if (value !== null && value !== undefined && value !== "" && weight > 0) {
        available.push([key, weight, Number(value)]);
      }
    });
    const total = available.reduce(function (sum, item) {
      return sum + item[1];
    }, 0);
    if (total <= 0 || available.length < floor) {
      return { score: null, used: {} };
    }
    const used = {};
    let score = 0;
    available.forEach(function (item) {
      const share = item[1] / total;
      used[item[0]] = share;
      score += share * item[2];
    });
    return { score: score, used: used };
  }

  return { combine: combine, keys: KEYS };
});
