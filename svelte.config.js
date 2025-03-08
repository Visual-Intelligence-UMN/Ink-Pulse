import adapter from '@sveltejs/adapter-static';
import preprocess from 'svelte-preprocess'
import sveltePreprocess from 'svelte-preprocess';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter({
			fallback: '404.html'
		}),
		paths: {
			base: process.argv.includes('dev') ? '' : '/Ink-Pulse',
			relative: false
		}
	}
};

export default {
	config,
}