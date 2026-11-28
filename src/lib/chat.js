export const STORAGE_KEY = "inkpulse_openai_api_key";

// LLM providers. Both take a key in the settings panel and are called the same way (sendChat).
// OpenAI goes through our Vercel route (gpt-4o). Bedrock is called directly from the browser
// (its OpenAI-compatible endpoint allows CORS) with a Bedrock API key as the bearer token.
export const PROVIDERS = {
  openai: { label: "OpenAI", storageKey: STORAGE_KEY },
  bedrock: { label: "Amazon Bedrock", storageKey: "inkpulse_bedrock_api_key" },
};
export const DEFAULT_PROVIDER = "openai";
const PROVIDER_STORAGE_KEY = "inkpulse_llm_provider";
const BEDROCK_CHAT_URL =
  "https://bedrock-mantle.us-east-2.api.aws/openai/v1/chat/completions";
export const BEDROCK_MODEL = "openai.gpt-5.6-terra";

export function storageKeyFor(provider) {
  return (PROVIDERS[provider] ?? PROVIDERS[DEFAULT_PROVIDER]).storageKey;
}

export function loadProvider() {
  if (typeof window === "undefined") return DEFAULT_PROVIDER;
  try {
    const saved = localStorage.getItem(PROVIDER_STORAGE_KEY);
    return saved in PROVIDERS ? saved : DEFAULT_PROVIDER;
  } catch {
    return DEFAULT_PROVIDER;
  }
}

export function saveProvider(provider) {
  if (typeof window === "undefined" || !(provider in PROVIDERS)) return;
  try {
    localStorage.setItem(PROVIDER_STORAGE_KEY, provider);
  } catch (error) {
    console.error("Failed to save LLM provider:", error);
  }
}

function decryptKey(encrypted) {
  if (!encrypted) return "";
  try {
    const secret = (
      navigator.userAgent +
      navigator.language +
      screen.width
    ).slice(0, 50);
    const decoded = atob(encrypted);

    const decrypted = decoded
      .split("")
      .map((char, i) => {
        const keyChar = secret.charCodeAt(i % secret.length);
        return String.fromCharCode(char.charCodeAt(0) ^ keyChar);
      })
      .join("");

    return decrypted;
  } catch (error) {
    console.warn("Decryption failed:", error);
    try {
      return atob(encrypted);
    } catch {
      return "";
    }
  }
}

export function loadApiKey(provider = loadProvider()) {
  if (typeof window === "undefined") return "";
  try {
    const encrypted = localStorage.getItem(storageKeyFor(provider));
    if (encrypted) {
      const decrypted = decryptKey(encrypted);
      // console.log("API Key loaded from storage");
      return decrypted;
    }
  } catch (error) {
    console.error("Failed to load API Key:", error);
  }
  return "";
}

export async function sendChat(
  systemPrompt,
  payload,
  apiKey,
  signal,
  provider = loadProvider(),
) {
  const messages = [
    { role: "system", content: systemPrompt },
    { role: "user", content: JSON.stringify(payload) },
  ];
  if (provider === "bedrock") return sendBedrockChat(messages, apiKey, signal);
  const response = await fetch("https://ink-pulse-one.vercel.app/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      apiKey,
      messages,
    }),
    signal,
  });
  const data = await response.json();
  if (!data.choices || data.choices.length === 0) {
    throw new Error(data.error?.message || "No choices returned from API");
  }
  return data.choices[0].message.content;
}

async function sendBedrockChat(messages, apiKey, signal) {
  if (!apiKey) throw new Error("Bedrock API key missing");
  const response = await fetch(BEDROCK_CHAT_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({ model: BEDROCK_MODEL, messages }),
    signal,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || !data.choices || data.choices.length === 0) {
    throw new Error(
      data.error?.message || data.message || `Bedrock request failed (HTTP ${response.status})`,
    );
  }
  return data.choices[0].message.content;
}
