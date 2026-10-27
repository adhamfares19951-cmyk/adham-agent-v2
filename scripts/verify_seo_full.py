# -*- coding: utf-8 -*-
import httpx
import sys
sys.stdout.reconfigure(encoding='utf-8')

r = httpx.get('http://127.0.0.1:8080/glamp')
print('Status:', r.status_code)
print('Has FAQ Schema:', 'FAQPage' in r.text)
print('Has Product Schema:', 'Product' in r.text)
print('Has Preload:', 'rel="preload"' in r.text)
print('Has FAQ Section:', 'الأسئلة الشائعة حول مصباح G-Lamp' in r.text)
print('Has Footer Brand:', 'Smart Store GCC' in r.text)
