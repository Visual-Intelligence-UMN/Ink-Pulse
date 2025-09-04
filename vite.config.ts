import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import Icons from 'unplugin-icons/vite';

export default defineConfig({
  base: process.env.NODE_ENV === 'development' ? '/' : '/Ink-Pulse/',
  plugins: [
    sveltekit(),
    Icons({
      compiler: 'svelte'
    }),
  ],
  ssr: {
    noExternal: ['virtua']
  }
});
