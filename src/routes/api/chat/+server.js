import { json } from '@sveltejs/kit';

export async function POST({ request }) {
  const { apiKey, messages } = await request.json();

  if (!apiKey) {
    return json({ error: 'API key missing' }, { status: 400 });
  }

  const response = await fetch(
    'https://api.openai.com/v1/chat/completions',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'gpt-4o',
        messages
      })
    }
  );

  const data = await response.json();
  return json(data);
}