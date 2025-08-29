export const topicIcons = {
    reincarnation: "🔄", 
    bee: "🐝",          
    sideeffect: "⚡",   
    pig: "🐖", 
    obama: "🏛️", 
    mana: "✨", 
    dad: "👨",  
    mattdamon: "🎬", 
    shapeshifter: "🌀",
    isolation: "🏝️",
    policy: "📋"
  };

export function getCategoryIcon(promptCode, dataset = "creative") {
  // For creative dataset, use emoji icons
  if (dataset === "creative" && topicIcons[promptCode]) {
    return topicIcons[promptCode];
  }
  
  // For other datasets, wrap letters in a styled span
  if (promptCode && dataset !== "creative") {
    const letters = promptCode.slice(0, 2).toUpperCase();
    return `<span class="topic-letters">${letters}</span>`;
  }
  
  // Fallback for creative dataset without match or empty promptCode
  return topicIcons[promptCode] || "📄"; 
}
