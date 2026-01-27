import adapterStatic from '@sveltejs/adapter-static';
import adapterVercel from '@sveltejs/adapter-vercel';

/** @type {import('@sveltejs/kit').Config} */
const isVercel = process.env.VERCEL === '1';

const config = {
  kit: {
    adapter: isVercel
      ? adapterVercel()
      : adapterStatic({
          pages: 'build',
          assets: 'build',
          fallback: '404.html'
        }),
    paths: {
      base: isVercel ? '' : '/Ink-Pulse',
      relative: false
    }
  }
};

export default config;