export async function onRequestPost(context) {
  try {
    const body = await context.request.json();
    const targetUrl = 'https://necklace-include-tunnel-morris.trycloudflare.com/api/order';
    
    const response = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'CloudflarePages-Proxy/1.0'
      },
      body: JSON.stringify(body)
    });
    
    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  } catch (err) {
    return new Response(JSON.stringify({ success: false, error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
