export const STORAGE_KEY = "inkpulse_openai_api_key";

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

export function loadApiKey() {
  if (typeof window === "undefined") return "";
  try {
    const encrypted = localStorage.getItem(STORAGE_KEY);
    if (encrypted) {
      const decrypted = decryptKey(encrypted);
      console.log("API Key loaded from storage");
      return decrypted;
    }
  } catch (error) {
    console.error("Failed to load API Key:", error);
  }
  return "";
}

export async function sendChat(systemPrompt, payload, apiKey, signal) {
  const response = await fetch("https://ink-pulse-one.vercel.app/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      apiKey,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: JSON.stringify(payload) },
      ],
    }),
    signal,
  });
  const data = await response.json();
  if (!data.choices || data.choices.length === 0) {
    throw new Error(data.error?.message || "No choices returned from API");
  }
  return data.choices[0].message.content;
}
