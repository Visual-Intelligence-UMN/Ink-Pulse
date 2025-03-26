<script lang="ts">
    export let chartData: any[] = [];
    const boxWidth = 0.1;
    const boxHeight = 10;
  </script>
  
  <svg width = {boxWidth * chartData.length}>
    {#each chartData as d, i}
        <rect
            x={boxWidth * i}
            y={boxHeight}
            width={boxWidth}
            height={boxHeight}
            fill={d.color}
        />
    {/each}

  </svg>
  