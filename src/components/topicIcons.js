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
    isolation: "🏝️" 
  };
export function getCategoryIcon(promptCode) {
  return topicIcons[promptCode] || "📄"; 
}
