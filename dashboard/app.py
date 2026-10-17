from flask import Flask, render_template_string, jsonify, request
import os

app = Flask(__name__)

# Simple dashboard template using Tailwind CDN for quick styling
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang='ar'>
<head>
  <meta charset='UTF-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1.0'>
  <title>مركز قيادة أدهم</title>
  <script src='https://cdn.tailwindcss.com'></script>
</head>
<body class='bg-gray-900 text-gray-100 min-h-screen flex flex-col'>
  <header class='bg-gray-800 p-4 shadow-md'>
    <h1 class='text-2xl font-bold text-center'>مركز قيادة أدهم</h1>
  </header>
  <main class='flex-1 p-4'>
    <section class='grid grid-cols-1 md:grid-cols-2 gap-4'>
      <!-- Sales & Leads -->
      <div class='bg-gray-800 rounded-lg p-4'>
        <h2 class='text-xl font-semibold mb-2'>المبيعات والـ Leads</h2>
        <button onclick='runAction("scrape")' class='w-full bg-blue-600 hover:bg-blue-500 text-white py-2 rounded'>مسح المحلات القريبة</button>
        <button onclick='runAction("pitch")' class='w-full bg-green-600 hover:bg-green-500 text-white py-2 rounded mt-2'>إرسال عرض</button>
        <div id='leads-output' class='mt-2 text-sm'></div>
      </div>
      <!-- Network & System -->
      <div class='bg-gray-800 rounded-lg p-4'>
        <h2 class='text-xl font-semibold mb-2'>الشبكة والنظام</h2>
        <button onclick='runAction("tunnel")' class='w-full bg-purple-600 hover:bg-purple-500 text-white py-2 rounded'>تشغيل نفق</button>
        <button onclick='runAction("diag")' class='w-full bg-indigo-600 hover:bg-indigo-500 text-white py-2 rounded mt-2'>تشخيص DNS</button>
        <div id='network-output' class='mt-2 text-sm'></div>
      </div>
      <!-- Media Production -->
      <div class='bg-gray-800 rounded-lg p-4'>
        <h2 class='text-xl font-semibold mb-2'>إنتاج محتوى</h2>
        <textarea id='video-script' rows='3' class='w-full bg-gray-700 text-white p-2 rounded' placeholder='اكتب نص الفيديو'></textarea>
        <button onclick='runAction("video")' class='w-full bg-red-600 hover:bg-red-500 text-white py-2 rounded mt-2'>إنشاء فيديو قصير</button>
        <div id='media-output' class='mt-2 text-sm'></div>
      </div>
      <!-- Finance -->
      <div class='bg-gray-800 rounded-lg p-4'>
        <h2 class='text-xl font-semibold mb-2'>المالية</h2>
        <button onclick='runAction("balance")' class='w-full bg-yellow-600 hover:bg-yellow-500 text-white py-2 rounded'>عرض الرصيد</button>
        <div id='finance-output' class='mt-2 text-sm'></div>
      </div>
    </section>
  </main>
  <footer class='bg-gray-800 p-2 text-center text-xs'>© 2026 أدهم • كل الحقوق محفوظة</footer>

  <script>
    async function runAction(action) {
      const outMap = {
        scrape: 'leads-output',
        pitch: 'leads-output',
        tunnel: 'network-output',
        diag: 'network-output',
        video: 'media-output',
        balance: 'finance-output'
      };
      const payload = {};
      if (action === 'video') {
        payload.text = document.getElementById('video-script').value;
      }
      const res = await fetch(`/api/${action}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      document.getElementById(outMap[action]).innerText = data.message || JSON.stringify(data);
    }
  </script>
</body>
</html>
"""

# Helper to simulate actions (replace with real calls later)
def fake_response(action, data=None):
    messages = {
        'scrape': 'تم مسح المحلات. عدد النتائج: 5',
        'pitch': 'تم إرسال عرض تجريبي للعميل.',
        'tunnel': 'النفق شغال على https://tube-convicted-linking-connectors.trycloudflare.com',
        'diag': 'تحقق من DNS: لا توجد مشاكل ملحوظة.',
        'video': f'تم إنشاء فيديو قصير من النص: {data.get("text", "")} (رابط تجريبي)',
        'balance': 'الرصيد الحالي: 2,350 ₪ (صافي)'
    }
    return {'status': 'ok', 'message': messages.get(action, 'تم تنفيذ الإجراء')}

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/<action>', methods=['POST'])
def api_action(action):
    data = request.get_json() or {}
    # In real implementation, call the corresponding tool via internal functions.
    # For now, return a placeholder.
    return jsonify(fake_response(action, data))

if __name__ == '__main__':
    # Bind to all interfaces so Cloudflare tunnel can reach it.
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
