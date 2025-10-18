<script>
  import { onMount } from 'svelte';
  import jStat from 'jstat';

  export let featureName;
  export let data; // selected data
  export let patternData; // compared data
  export let featureData // complete data
  export let flag; // whether compare with Others
  export let title;

  $: console.log("data", data);
  $: console.log("patternData", patternData);
  $: console.log("featureData", featureData);


  let canvas;


</script>

<canvas bind:this={canvas}></canvas>