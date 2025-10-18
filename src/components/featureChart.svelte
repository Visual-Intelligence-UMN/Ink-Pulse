<script>
  import { onMount } from 'svelte';
  import jStat from 'jstat';

  export let featureName;
  export let data; // selected data
  export let patternData; // compared data
  export let featureData // complete data
  export let flag; // whether compare with Others
  export let title;

  let canvas;


</script>

<canvas bind:this={canvas}></canvas>