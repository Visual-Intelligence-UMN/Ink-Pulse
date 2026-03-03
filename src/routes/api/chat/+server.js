import { json } from '@sveltejs/kit';

const ALLOWED_ORIGINS = new Set([
  'http://localhost:5173',
  'http://127.0.0.1:5173',
  'https://visual-intelligence-umn.github.io/Ink-Pulse/'
]);

function cors(origin) {
  if (!origin || !ALLOWED_ORIGINS.has(origin)) return {};
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin'
  };
}

export async function OPTIONS({ request }) {
  const origin = request.headers.get('origin');
  return new Response(null, { status: 204, headers: cors(origin) });
}

export async function POST({ request, fetch }) {
  const origin = request.headers.get('origin');
  const corsHeaders = cors(origin);

  if (!corsHeaders['Access-Control-Allow-Origin']) {
    return json({ error: 'CORS blocked for this origin', origin }, { status: 403 });
  }

  const { apiKey, messages } = await request.json();

  if (!apiKey) {
    return json({ error: 'API key missing' }, { status: 400, headers: corsHeaders });
  }

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: 'gpt-4o',
      messages
    })
  });

  const data = await response.json();
  return json(data, { status: response.status, headers: corsHeaders });
}