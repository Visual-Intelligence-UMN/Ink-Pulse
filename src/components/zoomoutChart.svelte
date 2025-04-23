<script lang="ts">
  import BarChartY from "./barChartY.svelte";
  export let chartData: any[] = [];
  export let sessionId;
  export let sessionTopic;
  const boxWidth = 0.1;
  const boxHeight = 10;
</script>
    
<svg width = {boxWidth * chartData.length + 1000}>
  <text
      x={boxWidth}
      y={boxHeight + 10}
      font-size=12px
      font-family="Poppins, sans-serif"
  >{sessionTopic}-{sessionId}</text>
  {#each chartData as d, i}
    <rect
        x={boxWidth * i + 350}
        y={boxHeight}
        width={boxWidth}
        height={boxHeight}
        fill={d.color}
    />
  {/each}
</svg>