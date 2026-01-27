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

// Generate a consistent color for each topic based on its name
function getTopicColor(promptCode) {
  // Create a simple hash from the prompt code
  let hash = 0;
  for (let i = 0; i < promptCode.length; i++) {
    const char = promptCode.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  
  // Use the hash to generate HSL colors with good contrast
  const hue = Math.abs(hash) % 360;
  const saturation = 65 + (Math.abs(hash) % 25); // 65-90%
  const lightness = 45 + (Math.abs(hash) % 15); // 45-60%
  
  return {
    primary: `hsl(${hue}, ${saturation}%, ${lightness}%)`,
    secondary: `hsl(${(hue + 30) % 360}, ${saturation - 10}%, ${lightness + 10}%)`,
    hover: `hsl(${(hue + 60) % 360}, ${saturation + 10}%, ${lightness - 5}%)`
  };
}

export function getCategoryIcon(promptCode, dataset = "creative") {
  // For creative dataset, use emoji icons
  if (dataset === "creative" && topicIcons[promptCode]) {
    return topicIcons[promptCode];
  }
  
  // For other datasets, wrap letters in a styled span with unique colors
  if (promptCode && dataset !== "creative") {
    const letters = promptCode.slice(0, 2).toUpperCase();
    const colors = getTopicColor(promptCode);
    
    return `<span class="topic-letters" data-topic="${promptCode}" style="--topic-color-primary: ${colors.primary}; --topic-color-secondary: ${colors.secondary}; --topic-color-hover: ${colors.hover};">${letters}</span>`;
  }
  
  // Fallback for creative dataset without match or empty promptCode
  return topicIcons[promptCode] || "📄"; 
}
