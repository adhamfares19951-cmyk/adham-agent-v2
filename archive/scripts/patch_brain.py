with open(r'C:\Projects\adham-agent\brain.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """  * مخدم الوسائط والويب: يعمل على البورت 8080 برابط عام: http://136.244.77.61:8080/"""

replacement = """  * مخدم الوسائط والرابط السحابي الدائم للمتجر والملفات والسير الذاتية: https://smartglamp.pages.dev/
  * 🚨 تحذير صارم: ممنوع منعاً باتاً كتابة روابط 136.244.77.61:8080 لأن هذا الآي بي معطل ولا يفتح من هواتف المستخدمين. أي رابط عام للملفات يجب أن يكون حصراً عبر: https://smartglamp.pages.dev/<اسم_الملف> أو يرسل كمستند Telegram Document.
  * 🚨 قاعدة منع الهلوسة في الملفات: ممنوع نهائياً أن تدعي أنك أنشأت ملفاً أو حفظته على سطح المكتب ما لم تكن الأداة قد نفذت بالفعل وتأكدت من مساره، وتكتب الرابط السحابي الحقيقي فقط."""

if target in text:
    text = text.replace(target, replacement, 1)
    with open(r'C:\Projects\adham-agent\brain.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully patched brain.py!")
else:
    print("Target not found in brain.py")
