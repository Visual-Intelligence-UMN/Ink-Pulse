import { bindAnchors, validateSpec } from "./patternSpec.js";

export const REFINE_SYSTEM_PROMPT = `You revise an existing validated PatternSpec in response to an analyst’s requested change.
Rules:
- Return an RFC 6902 JSON Patch only.
- Modify only fields required by the analyst’s request.
- Use only features and operations in the supplied feature catalog.
- Do not convert a soft attribute into a hard constraint unless the analyst explicitly requests that change.
- Do not invent numeric thresholds.
- Mark newly introduced fields with provenance “analyst-confirmed.”
- Do not modify the reference episode, segmentation configuration, or outcome-feature restrictions.
- If the request cannot be represented, return an empty patch and place the reason in the supplied unresolved-message field.
- Do not output SQL, executable code, Markdown, or explanatory prose outside the patch.

Response envelope (overrides patch-only formatting): return exactly { "patch": [RFC 6902 ops], "unresolved": "" }. Use only add, remove, or replace operations. If the patch is empty, put the reason in unresolved.
Both span bounds must remain unchanged; gap rules are not executed. Requests requiring either change are unrepresentable.`;

export function buildRefineInput(spec, catalog, userText) {
  return { current_spec: spec, feature_catalog: catalog, requested_change: userText };
}

const owns = (object, key) => Object.hasOwn(object, key);

function pointerParts(path) {
  if (path === "") return [];
  if (typeof path !== "string" || !path.startsWith("/") || /~(?:[^01]|$)/.test(path)) {
    throw new Error("invalid JSON Pointer");
  }
  return path.slice(1).split("/").map((part) => part.replace(/~1/g, "/").replace(/~0/g, "~"));
}

function arrayIndex(key, length, allowAppend = false) {
  if (allowAppend && key === "-") return length;
  if (!/^(0|[1-9][0-9]*)$/.test(key)) throw new Error(`invalid array index ${JSON.stringify(key)}`);
  const index = Number(key);
  if (!Number.isSafeInteger(index) || index > length || (!allowAppend && index === length)) {
    throw new Error(`array index ${key} is out of bounds`);
  }
  return index;
}

function existing(container, key) {
  if (container === null || typeof container !== "object") {
    throw new Error("path traverses a non-container");
  }
  const member = Array.isArray(container) ? arrayIndex(key, container.length) : key;
  if (!owns(container, member)) throw new Error(`path member ${JSON.stringify(key)} does not exist`);
  return member;
}

// JSON-only documents. Root removal returns undefined (no document); only
// a subsequent root add can create a document again. The caller validates the result.
export function applyPatch(spec, ops) {
  if (!Array.isArray(ops)) throw new Error("patch must be an array");
  let document = structuredClone(spec);
  for (const [index, operation] of ops.entries()) {
    try {
      if (!operation || typeof operation !== "object" || Array.isArray(operation)) {
        throw new Error("expected an operation object");
      }
      const { op, path } = operation;
      if (!owns(operation, "op") || !["add", "remove", "replace"].includes(op)) {
        throw new Error(`unsupported operation ${JSON.stringify(op)}`);
      }
      if (!owns(operation, "path")) throw new Error("missing path");
      const parts = pointerParts(path);
      if (op !== "remove" && !owns(operation, "value")) throw new Error("missing value");
      const value = op === "remove" ? undefined : structuredClone(operation.value);
      if (!parts.length) {
        if (op !== "add" && document === undefined) throw new Error("root does not exist");
        document = value;
        continue;
      }
      const key = parts.pop();
      let parent = document;
      for (const part of parts) parent = parent[existing(parent, part)];
      if (Array.isArray(parent)) {
        const i = op === "add" ? arrayIndex(key, parent.length, true) : existing(parent, key);
        if (op === "replace") parent[i] = value;
        else if (op === "remove") parent.splice(i, 1);
        else parent.splice(i, 0, value);
      } else {
        if (parent === null || typeof parent !== "object") throw new Error("path parent is not a container");
        if (op !== "add") existing(parent, key);
        if (op === "remove") delete parent[key];
        else Object.defineProperty(parent, key, { value, writable: true, enumerable: true, configurable: true });
      }
    } catch (error) {
      throw new Error(`patch[${index}] (${JSON.stringify(operation?.path)}): ${error.message}`, { cause: error });
    }
  }
  return document;
}

// Validate before binding so malformed patches never reach the evaluator.
export function validateRefineSpec(spec, catalog, referenceLength) {
  const result = validateSpec(spec, { catalog, referenceLength });
  if (!result.ok) throw new Error(`Invalid pattern spec: ${result.errors.join("; ")}`);
}

export function resolveRefineResponse(raw, originalSpec, catalog, reference) {
  const { patch, unresolved } = JSON.parse(raw) ?? {};
  if (!Array.isArray(patch) || typeof unresolved !== "string") {
    throw new Error("Expected a patch array and an unresolved message.");
  }
  if (!patch.length) return { unresolved: unresolved.trim() || "No changes could be made." };

  const patched = applyPatch(originalSpec, patch);
  validateRefineSpec(patched, catalog, reference.length);
  const gapFields = ["left", "right", "min_blocks", "max_blocks", "constrain_intermediate"];
  if (JSON.stringify(patched.span.gaps, gapFields) !== JSON.stringify(originalSpec.span.gaps, gapFields)) {
    throw new Error("Gap rules cannot be revised in a fixed-window search.");
  }
  const bound = bindAnchors(patched, reference);
  if (!bound.ok) throw new Error(`Anchor binding failed: ${bound.errors.join("; ")}`);
  return { spec: bound.spec };
}
