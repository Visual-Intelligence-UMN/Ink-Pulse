// Fig. 11 typed forms (schema version 1.0). Keys with ? are optional.
// Source = "user" | "api" (Human | AI); Num = finite number.
// NumericOp = "=" | "<" | "<=" | ">" | ">="; source uses only "=".
// BlockRef = {offset: integer} | {anchor_id: id}; offsets are zero-based.
// FeatureRef = BlockRef & {feature_id?: id} (defaults to the constraint feature).
// Predicate = {feature_id: id, operator: NumericOp, value: Num | Source}.
// Anchor.selector = "first-matching" | "last-matching" | "first-matching-after";
// after is null except for the last form, which requires an earlier anchor ID.
// Anchor.offset? is stored after binding. Gap objects use Fig. 11 fields as written.
// Attribute.scope = BlockRef | {window: true, source?: Source}.
// Attribute.expected = {value: Num | Source} | {operator: NumericOp, value: Num | Source}
//                    | {trend: "increasing" | "decreasing"}.
// Constraint left / right by type:
//   source:           BlockRef / {value: Source}
//                     or {sequence: true} / {reference: true, sources?: Source[]}.
//   scalar:           BlockRef / {value: Num}.
//   pairwise:         BlockRef / FeatureRef.
//   ratio:            {numerator: BlockRef, denominator: FeatureRef} / {value: Num, alternatives?: Num[]}.
//   trend:            {source: Source} / {value: 0}, using "<" or ">".
//   count:            {predicate: Predicate} / {value: nonnegative safe integer}.
//   aggregate:        Aggregate / {value: Num} or (Aggregate & {feature_id?: id}).
//   session-position: {offset: 0} or {anchor_id: id} / {value: Num in [0,1]}.
// Aggregate = {aggregate: "min" | "max" | "mean" | "sum", source?: Source}.
// Provenance = "user-description" | "reference-example" | "system-default" | "analyst-confirmed".
// Catalog entries supply id, level ("block"), value_type ("source" or "number"), unit, role,
// and operations (a map from constraint type to allowed operators).

// Absolute tolerance in the compared units. Strict comparisons exclude the equality band;
// inclusive comparisons include it. This does not relax the ratio denominator's R > 0 rule.
const EPSILON = 1e-9;
const operators = ["=", "<", "<=", ">", ">="];
const provenance = ["user-description", "reference-example", "system-default", "analyst-confirmed"];
const anchorSelectors = ["first-matching", "last-matching", "first-matching-after"];
const reducers = ["min", "max", "mean", "sum"];
const axes = ["time", "progress"];
const types = ["source", "scalar", "pairwise", "ratio", "trend", "count", "aggregate", "session-position"];

const owns = (object, key) => Object.hasOwn(object, key);
const record = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const text = (value) => typeof value === "string" && value.trim().length > 0;
const source = (value) => value === "user" || value === "api";
const finite = Number.isFinite;
const natural = (value) => Number.isSafeInteger(value) && value >= 0;
const featureEntry = (catalog, id) => Array.isArray(catalog) ? catalog.find((entry) => entry?.id === id) : undefined;

// Check once before binding/evaluation. Errors are annotated with the JSON field path.
/** @param {any} spec @param {{catalog?: object[], referenceLength?: number}} [options] */
export function validateSpec(spec, { catalog, referenceLength } = {}) {
  const errors = [];
  const ids = new Set();
  const anchors = new Map();
  const targets = new Set();
  const fail = (path, message) => errors.push(`${path}: ${message}`);
  const result = () => ({ ok: errors.length === 0, errors });

  function shape(value, path, required, optional = []) {
    if (!record(value)) {
      fail(path, "expected an object");
      return false;
    }
    for (const key of required) {
      if (!owns(value, key)) fail(`${path}.${key}`, "required field");
    }
    for (const key of Object.keys(value)) {
      if (!required.includes(key) && !optional.includes(key)) fail(`${path}.${key}`, "unknown field");
    }
    return true;
  }

  function list(items, path, visit) {
    if (!Array.isArray(items)) {
      fail(path, "expected an array");
      return;
    }
    for (let i = 0; i < items.length; i++) visit(items[i], `${path}[${i}]`, i);
  }

  function unique(id, path) {
    if (!text(id)) fail(path, "expected a nonblank ID");
    else if (ids.has(id)) fail(path, `duplicate ID ${id}`);
    else {
      ids.add(id);
      return true;
    }
    return false;
  }

  function offset(value, path) {
    if (!natural(value) || !(value < referenceLength)) fail(path, "offset outside reference window");
  }

  function feature(id, path, { type = undefined, operator = undefined, valueType = undefined, attribute = false } = {}) {
    const entry = text(id) ? featureEntry(catalog, id) : undefined;
    if (!entry) {
      fail(path, "unknown catalog feature");
      return;
    }
    if (entry.role === "outcome") fail(path, "outcome features cannot be used in a search");
    if (attribute && entry.role === "constraint-only") fail(path, "feature is constraint-only");
    if (entry.level !== "block") fail(path, "feature must be block-level");
    if (entry.value_type !== "number" && entry.value_type !== "source") fail(path, "unsupported feature value type");
    if (valueType && entry.value_type !== valueType) fail(path, `expected a ${valueType} feature`);
    if (type) {
      const supported = entry.operations?.[type];
      if (!Array.isArray(supported) || !supported.includes(operator)) fail(path, `feature does not support ${type} ${operator}`);
    }
    return entry;
  }

  function sourceFilter(value, path) {
    if (!source(value)) fail(path, "expected user or api");
    feature("source", path, { type: "source", operator: "=", valueType: "source" });
  }

  function literal(value, path, valueType) {
    if (valueType === "source" ? !source(value) : !finite(value)) {
      fail(path, valueType === "source" ? "expected user or api" : "expected a finite number");
    }
  }

  function comparison(operator, path, valueType) {
    if (!operators.includes(operator) || (valueType === "source" && operator !== "=")) {
      fail(path, "unsupported comparison operator");
    }
  }

  function blockRef(value, path, withFeature = false) {
    const byOffset = record(value) && owns(value, "offset");
    if (!shape(value, path, [byOffset ? "offset" : "anchor_id"], withFeature ? ["feature_id"] : [])) return;
    if (byOffset) offset(value.offset, `${path}.offset`);
    else if (!anchors.has(value.anchor_id)) fail(`${path}.anchor_id`, "unknown anchor");
  }

  function predicate(value, path, expectedFeature = undefined) {
    if (!shape(value, path, ["feature_id", "operator", "value"])) return;
    if (expectedFeature !== undefined && value.feature_id !== expectedFeature) {
      fail(`${path}.feature_id`, "must match the count feature");
    }
    const valueType = featureEntry(catalog, value.feature_id)?.value_type;
    feature(value.feature_id, `${path}.feature_id`, {
      type: valueType === "source" ? "source" : "scalar", operator: value.operator,
    });
    comparison(value.operator, `${path}.operator`, valueType);
    literal(value.value, `${path}.value`, valueType);
  }

  function compatible(left, selector, constraint, path) {
    if (!record(selector) || !owns(selector, "feature_id")) return;
    const right = feature(selector.feature_id, `${path}.feature_id`, {
      type: constraint.type, operator: constraint.operator, valueType: "number",
    });
    if (left && right && left.id !== right.id && (!text(left.unit) || left.unit !== right.unit)) {
      fail(`${path}.feature_id`, "comparison requires matching catalog units");
    }
  }

  function aggregate(value, path, withFeature = false) {
    if (!shape(value, path, ["aggregate"], withFeature ? ["source", "feature_id"] : ["source"])) return;
    if (!reducers.includes(value.aggregate)) fail(`${path}.aggregate`, "expected min, max, mean or sum");
    if (owns(value, "source")) sourceFilter(value.source, `${path}.source`);
  }

  function numberValue(value, path, optional = []) {
    if (shape(value, path, ["value"], optional)) literal(value.value, `${path}.value`, "number");
  }

  if (!natural(referenceLength) || referenceLength === 0) fail("referenceLength", "expected a positive safe integer");
  if (!Array.isArray(catalog)) fail("catalog", "expected an array");
  if (!shape(spec, "spec", ["schema_version", "span", "attributes", "constraints", "assumptions", "unresolved", "explanations"])) return result();
  if (spec.schema_version !== "1.0") fail("schema_version", 'expected "1.0"');

  if (shape(spec.span, "span", ["min_blocks", "max_blocks", "anchors", "gaps"])) {
    for (const key of ["min_blocks", "max_blocks"]) {
      if (!natural(spec.span[key]) || spec.span[key] === 0 || spec.span[key] !== referenceLength) {
        fail(`span.${key}`, "must equal the positive reference length");
      }
    }
    let lastOffset = -1;
    list(spec.span.anchors, "span.anchors", (anchor, path, index) => {
      if (!shape(anchor, path, ["id", "selector", "after", "predicate"], ["offset"])) return;
      if (!anchorSelectors.includes(anchor.selector)) fail(`${path}.selector`, "unknown anchor selector");
      if (anchor.selector === "first-matching-after") {
        if (!anchors.has(anchor.after)) fail(`${path}.after`, "must name a preceding anchor");
      } else if (anchor.after !== null) fail(`${path}.after`, "must be null for this selector");
      if (owns(anchor, "offset")) {
        offset(anchor.offset, `${path}.offset`);
        if (natural(anchor.offset)) {
          if (anchor.offset <= lastOffset) fail(`${path}.offset`, "bound anchors must be in increasing order");
          lastOffset = anchor.offset;
        }
      }
      if (unique(anchor.id, `${path}.id`)) anchors.set(anchor.id, index);
      predicate(anchor.predicate, `${path}.predicate`);
    });
    // Fixed-length execution does not run gap rules. Keep and validate them for the paper format.
    list(spec.span.gaps, "span.gaps", (gap, path) => {
      if (!shape(gap, path, ["left", "right", "min_blocks", "max_blocks", "constrain_intermediate"])) return;
      for (const key of ["left", "right"]) {
        if (!anchors.has(gap[key])) fail(`${path}.${key}`, "unknown anchor");
      }
      if (anchors.get(gap.left) >= anchors.get(gap.right)) fail(path, "left anchor must precede right anchor");
      for (const key of ["min_blocks", "max_blocks"]) {
        if (!natural(gap[key])) fail(`${path}.${key}`, "expected a nonnegative safe integer");
      }
      if (natural(gap.min_blocks) && natural(gap.max_blocks) && gap.min_blocks > gap.max_blocks) fail(path, "minimum gap cannot exceed maximum");
      if (typeof gap.constrain_intermediate !== "boolean") fail(`${path}.constrain_intermediate`, "expected a boolean");
    });
  }

  list(spec.attributes, "attributes", (entry, path) => {
    if (!shape(entry, path, ["id", "feature_id", "scope", "expected", "priority", "provenance"])) return;
    if (unique(entry.id, `${path}.id`)) targets.add(entry.id);
    const valueType = feature(entry.feature_id, `${path}.feature_id`, { attribute: true })?.value_type;
    if (!provenance.includes(entry.provenance)) fail(`${path}.provenance`, "invalid provenance");
    if (!["primary", "secondary"].includes(entry.priority)) fail(`${path}.priority`, "expected primary or secondary");
    const { scope, expected } = entry;
    if (record(scope) && owns(scope, "window")) {
      shape(scope, `${path}.scope`, ["window"], ["source"]);
      if (scope.window !== true) fail(`${path}.scope.window`, "expected true");
      if (owns(scope, "source")) sourceFilter(scope.source, `${path}.scope.source`);
    } else blockRef(scope, `${path}.scope`);
    if (record(expected) && owns(expected, "trend")) {
      shape(expected, `${path}.expected`, ["trend"]);
      if (!["increasing", "decreasing"].includes(expected.trend)) fail(`${path}.expected.trend`, "expected increasing or decreasing");
      feature(entry.feature_id, `${path}.expected`, {
        type: "trend", operator: expected.trend === "increasing" ? ">" : "<", valueType: "number",
      });
    } else if (record(expected) && owns(expected, "operator")) {
      shape(expected, `${path}.expected`, ["operator", "value"]);
      feature(entry.feature_id, `${path}.expected`, {
        type: valueType === "source" ? "source" : "scalar", operator: expected.operator,
      });
      comparison(expected.operator, `${path}.expected.operator`, valueType);
      literal(expected.value, `${path}.expected.value`, valueType);
    } else if (shape(expected, `${path}.expected`, ["value"])) {
      literal(expected.value, `${path}.expected.value`, valueType);
    }
  });

  list(spec.constraints, "constraints", (constraint, path) => {
    if (!shape(constraint, path, ["id", "type", "feature_id", "left", "operator", "right", "provenance"])) return;
    if (unique(constraint.id, `${path}.id`)) targets.add(constraint.id);
    if (!provenance.includes(constraint.provenance)) fail(`${path}.provenance`, "invalid provenance");
    const { type, feature_id: id, left, operator, right } = constraint;
    if (!types.includes(type)) {
      fail(`${path}.type`, "unsupported constraint type");
      return;
    }
    const a = `${path}.left`;
    const b = `${path}.right`;
    const entry = feature(id, `${path}.feature_id`, {
      type, operator, valueType: type === "source" ? "source" : type === "count" ? undefined : "number",
    });
    comparison(operator, `${path}.operator`, type === "source" ? "source" : "number");
    switch (type) {
      case "source":
        if (id !== "source") fail(`${path}.feature_id`, "must be source");
        if (record(left) && owns(left, "sequence")) {
          shape(left, a, ["sequence"]);
          if (left.sequence !== true) fail(`${a}.sequence`, "expected true");
          if (shape(right, b, ["reference"], ["sources"])) {
            if (right.reference !== true) fail(`${b}.reference`, "expected true");
            if (owns(right, "sources")) {
              if (right.sources?.length !== referenceLength) fail(`${b}.sources`, "expected one source per reference block");
              list(right.sources, `${b}.sources`, (value, field) => literal(value, field, "source"));
            }
          }
        } else {
          blockRef(left, a);
          if (shape(right, b, ["value"])) literal(right.value, `${b}.value`, "source");
        }
        break;
      case "scalar":
        blockRef(left, a);
        numberValue(right, b);
        break;
      case "pairwise":
        blockRef(left, a);
        blockRef(right, b, true);
        compatible(entry, right, constraint, b);
        break;
      case "ratio":
        if (shape(left, a, ["numerator", "denominator"])) {
          blockRef(left.numerator, `${a}.numerator`);
          blockRef(left.denominator, `${a}.denominator`, true);
          compatible(entry, left.denominator, constraint, `${a}.denominator`);
        }
        numberValue(right, b, ["alternatives"]);
        if (record(right) && owns(right, "alternatives")) list(right.alternatives, `${b}.alternatives`, (value, field) => literal(value, field, "number"));
        break;
      case "trend":
        if (shape(left, a, ["source"])) sourceFilter(left.source, `${a}.source`);
        if (shape(right, b, ["value"]) && right.value !== 0) fail(`${b}.value`, "trend compares slope with zero");
        if (operator !== "<" && operator !== ">") fail(`${path}.operator`, "trend requires < or >");
        break;
      case "count":
        if (shape(left, a, ["predicate"])) predicate(left.predicate, `${a}.predicate`, id);
        if (shape(right, b, ["value"]) && !natural(right.value)) fail(`${b}.value`, "expected a nonnegative safe integer");
        break;
      case "aggregate":
        aggregate(left, a);
        if (record(right) && owns(right, "aggregate")) {
          aggregate(right, b, true);
          compatible(entry, right, constraint, b);
        } else numberValue(right, b);
        break;
      case "session-position":
        if (!axes.includes(id)) fail(`${path}.feature_id`, "expected time or progress");
        blockRef(left, a);
        if (record(left) && owns(left, "offset") && left.offset !== 0) fail(`${a}.offset`, "use window start (offset 0) or an anchor");
        if (shape(right, b, ["value"]) && (!finite(right.value) || right.value < 0 || right.value > 1)) {
          fail(`${b}.value`, "expected a number in [0,1]");
        }
        break;
    }
  });

  list(spec.assumptions, "assumptions", (value, path) => {
    if (!text(value)) fail(path, "expected nonblank text");
  });
  list(spec.unresolved, "unresolved", (value, path) => {
    if (!shape(value, path, ["term", "message"])) return;
    for (const key of ["term", "message"]) {
      if (!text(value[key])) fail(`${path}.${key}`, "expected nonblank text");
    }
  });
  list(spec.explanations, "explanations", (value, path) => {
    if (!shape(value, path, ["target_id", "text"])) return;
    if (!targets.has(value.target_id)) fail(`${path}.target_id`, "unknown constraint or attribute");
    if (!text(value.text)) fail(`${path}.text`, "expected nonblank text");
  });
  return result();
}

function blockValue(block, id) {
  if (!block) return undefined;
  if (id === "source") return source(block.source) ? block.source : undefined;
  if (axes.includes(id)) {
    const start = block[`start_${id}`];
    const end = block[`end_${id}`];
    const delta = finite(start) && finite(end) ? end - start : undefined;
    return finite(delta) ? delta : undefined;
  }
  const value = block[id === "semantic_change" ? "residual_vector_norm" : id];
  return finite(value) ? value : undefined;
}

function compare(left, operator, right) {
  if (source(left) && source(right)) return operator === "=" && left === right;
  if (!finite(left) || !finite(right)) return false;
  const difference = left - right;
  switch (operator) {
    case "=": return Math.abs(difference) <= EPSILON;
    case "<": return difference < -EPSILON;
    case "<=": return difference <= EPSILON;
    case ">": return difference > EPSILON;
    case ">=": return difference >= -EPSILON;
    default: return false;
  }
}

// undefined is distinct from a known non-match (needed when counting).
function matches(block, predicate) {
  const actual = blockValue(block, predicate.feature_id);
  return actual === undefined ? undefined : compare(actual, predicate.operator, predicate.value);
}

// Run on a validated draft and canonical reference blocks. Does not modify either input.
export function bindAnchors(spec, referenceBlocks) {
  const reject = (error) => ({ ok: false, spec: null, errors: [error] });
  const n = spec.span.min_blocks;
  if (!Array.isArray(referenceBlocks) || referenceBlocks.length !== n || spec.span.max_blocks !== n) {
    return reject("referenceBlocks: expected the fixed reference length");
  }
  const offsets = new Map();
  const anchors = [];
  let previous = -1;
  for (const anchor of spec.span.anchors) {
    const last = anchor.selector === "last-matching";
    const start = last ? n - 1 : anchor.selector === "first-matching-after" ? offsets.get(anchor.after) + 1 : 0;
    let offset = start;
    while (offset >= 0 && offset < n && !matches(referenceBlocks[offset], anchor.predicate)) offset += last ? -1 : 1;
    if (!(offset >= 0 && offset < n)) return reject(`anchor ${anchor.id}: no matching reference block`);
    if (offset <= previous) return reject(`anchor ${anchor.id}: reference anchors are not in increasing order`);
    previous = offset;
    offsets.set(anchor.id, offset);
    anchors.push({ ...anchor, offset });
  }
  let lockedSources;
  const constraints = [];
  for (const constraint of spec.constraints) {
    if (constraint.type === "source" && constraint.left.sequence) {
      lockedSources ??= Array.from(referenceBlocks, (block) => blockValue(block, "source"));
      if (lockedSources.includes(undefined)) return reject(`constraint ${constraint.id}: reference source is missing`);
      constraints.push({ ...constraint, right: { reference: true, sources: lockedSources } });
    } else constraints.push(constraint);
  }
  return { ok: true, spec: { ...spec, span: { ...spec.span, anchors }, constraints }, errors: [] };
}

function selectedValues(blocks, id, contributor) {
  const values = [];
  for (const block of blocks) {
    if (contributor !== undefined) {
      const actual = blockValue(block, "source");
      if (actual === undefined) return;
      if (actual !== contributor) continue;
    }
    const value = blockValue(block, id);
    if (value === undefined) return;
    values.push(value);
  }
  return values;
}

function slope(values) {
  if (!values || values.length < 2) return;
  const mid = (values.length - 1) / 2;
  let numerator = 0;
  let denominator = 0;
  // Centered indices sum to zero, so subtracting the mean of y is unnecessary.
  for (let i = 0; i < values.length; i++) {
    const x = i - mid;
    numerator += x * values[i];
    denominator += x ** 2;
  }
  return numerator / denominator;
}

function summarize(blocks, id, selector) {
  const values = selectedValues(blocks, selector.feature_id ?? id, selector.source);
  if (!values?.length) return;
  switch (selector.aggregate) {
    case "min": return values.reduce((a, b) => Math.min(a, b));
    case "max": return values.reduce((a, b) => Math.max(a, b));
    case "sum": return values.reduce((a, b) => a + b, 0);
    case "mean": return values.reduce((a, b) => a + b, 0) / values.length;
  }
}

function sessionPosition(block, id, bounds) {
  const value = block?.[`start_${id}`];
  if (!finite(value) || !finite(bounds?.start) || !finite(bounds?.end)) return;
  const range = bounds.end - bounds.start;
  if (!finite(range) || range <= 0 || value < bounds.start || value > bounds.end) return;
  return (value - bounds.start) / range;
}

// Evaluate the hard part of a validated, bound spec. The caller supplies the same catalog
// used to validate it and whole-session {start, end} for any used position axis.
/** @param {any} spec @param {any[]} windowBlocks
 * @param {{catalog?: object[], time?: {start: number, end: number}, progress?: {start: number, end: number}}} [sessionContext]
 */
export function evaluateSpec(spec, windowBlocks, sessionContext = {}) {
  if (!Array.isArray(windowBlocks) || windowBlocks.length !== spec.span.min_blocks ||
      windowBlocks.length !== spec.span.max_blocks) return { pass: false, failed: [] };

  const offsets = new Map();
  const failed = [];
  const catalog = sessionContext.catalog;
  const usable = (id) => {
    const entry = featureEntry(catalog, id);
    return entry?.level === "block" && entry.role !== "outcome";
  };
  for (const anchor of spec.span.anchors) {
    const { id, offset, predicate } = anchor;
    if (natural(offset) && offset < windowBlocks.length) offsets.set(id, offset);
    if (!offsets.has(id) || !usable(predicate.feature_id) || !matches(windowBlocks[offset], predicate)) failed.push(id);
  }

  const block = (ref) => windowBlocks[ref.offset ?? offsets.get(ref.anchor_id)];
  const read = (id, ref) => {
    const feature = ref.feature_id ?? id;
    return usable(feature) ? blockValue(block(ref), feature) : undefined;
  };
  function passes(constraint) {
    const { type, feature_id: id, left, operator, right } = constraint;
    if (!usable(id)) return false;
    switch (type) {
      case "source":
        if (left.sequence) {
          return right.sources?.length === windowBlocks.length &&
            right.sources.every((expected, i) => source(expected) && blockValue(windowBlocks[i], id) === expected);
        }
        return compare(read(id, left), operator, right.value);
      case "scalar": return compare(read(id, left), operator, right.value);
      case "pairwise": return compare(read(id, left), operator, read(id, right));
      case "ratio": {
        const numerator = read(id, left.numerator);
        const denominator = read(id, left.denominator);
        return finite(numerator) && finite(denominator) && denominator > 0 &&
          compare(numerator / denominator, operator, right.value);
      }
      case "trend": return compare(slope(selectedValues(windowBlocks, id, left.source)), operator, right.value);
      case "count": {
        let count = 0;
        for (const item of windowBlocks) {
          const match = matches(item, left.predicate);
          if (match === undefined) return false;
          if (match) count++;
        }
        return compare(count, operator, right.value);
      }
      case "aggregate": {
        const rhs = right.aggregate
          ? usable(right.feature_id ?? id) ? summarize(windowBlocks, id, right) : undefined
          : right.value;
        return compare(summarize(windowBlocks, id, left), operator, rhs);
      }
      case "session-position": return compare(sessionPosition(block(left), id, sessionContext[id]), operator, right.value);
      default: return false;
    }
  }
  for (const constraint of spec.constraints) {
    if (!passes(constraint)) failed.push(constraint.id);
  }
  return { pass: failed.length === 0, failed };
}
