export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Proxy POST /api/order directly to our backend server
    if (request.method === "POST" && (url.pathname === "/api/order" || url.pathname.endsWith("/order"))) {
      try {
        const body = await request.text();
        const targetUrl = "https://necklace-include-tunnel-morris.trycloudflare.com/api/order";
        const proxyResp = await fetch(targetUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "User-Agent": "CloudflareWorker-Proxy/1.0"
          },
          body: body
        });
        const respText = await proxyResp.text();
        return new Response(respText, {
          status: proxyResp.status,
          headers: {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
          }
        });
      } catch (err) {
        return new Response(JSON.stringify({ success: false, error: err.message }), {
          status: 500,
          headers: { "Content-Type": "application/json" }
        });
      }
    }

    // Serve static files from dist_pages
    return env.ASSETS.fetch(request);
  }
};
