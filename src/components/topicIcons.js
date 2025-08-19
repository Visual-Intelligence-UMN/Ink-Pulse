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
export function getCategoryIcon(promptCode) {
  return topicIcons[promptCode] || "📄"; 
}
