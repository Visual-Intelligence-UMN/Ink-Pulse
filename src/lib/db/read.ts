import { browser } from "$app/environment";

export async function readSegmentResults(dataset: string) {
  if (browser) {
    const { readSegmentResultsBrowser } = await import("./read.browser.js");
    return readSegmentResultsBrowser(dataset);
  } else {
    const { readSegmentResultsNode } = await import("./read.node.js");
    return readSegmentResultsNode(dataset);
  }
}
