// src/utils/parseLayout.js
// Utility to extract and parse valid JSON from LLM responses or raw strings.

export function parseLayoutString(raw) {
  if (!raw) return null;

  // If it's already a JS object, just return it
  if (typeof raw === "object") return raw;

  // --- Step 1: Try direct JSON.parse (fast path)
  try {
    return JSON.parse(raw);
  } catch (_) {}

  // --- Step 2: Try to extract a ```json ... ``` fenced block
  const jsonBlockMatch = raw.match(/```json\s*([\s\S]*?)```/i);
  if (jsonBlockMatch) {
    const jsonStr = jsonBlockMatch[1].trim();
    try {
      return JSON.parse(jsonStr);
    } catch (_) {}
  }

  // --- Step 3: Try any generic code fence ``` ... ```
  const genericBlockMatch = raw.match(/```([\s\S]*?)```/);
  if (genericBlockMatch) {
    const jsonStr = genericBlockMatch[1].trim();
    try {
      return JSON.parse(jsonStr);
    } catch (_) {}
  }

  // --- Step 4: Fallback to first {...} ... } region
  const first = raw.indexOf("{");
  const last = raw.lastIndexOf("}");
  if (first !== -1 && last !== -1 && last > first) {
    const candidate = raw.slice(first, last + 1).trim();
    try {
      return JSON.parse(candidate);
    } catch (_) {}
  }

  // --- Step 5: Final attempt — clean weird Markdown leftovers
  const cleaned = raw
    .replace(/^[^\[{]+/, "") // remove text before JSON start
    .replace(/```+/g, "") // remove code fences
    .replace(/json/i, "") // remove 'json' keywords
    .trim();

  try {
    return JSON.parse(cleaned);
  } catch (_) {}

  // --- Step 6: Give up gracefully
  console.warn("parseLayoutString: failed to parse layout:", raw);
  return null;
}
