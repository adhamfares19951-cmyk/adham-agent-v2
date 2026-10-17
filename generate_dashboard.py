import matplotlib.pyplot as plt
import numpy as np

# إعداد شكل الداشبورد بستايل احترافي (Dark Theme)
fig, ax = plt.subplots(figsize=(1080/100, 1920/100))
fig.patch.set_facecolor('#050505')
ax.set_facecolor('#050505')

# بيانات وهمية للشارت
x = np.arange(50)
y = np.random.randn(50).cumsum()

# رسم الشارت
ax.plot(x, y, color='#00ff9d', linewidth=3, alpha=0.8)
ax.fill_between(x, y, y.min(), color='#00ff9d', alpha=0.1)

# إعدادات المحاور
ax.spines['bottom'].set_color('#333')
ax.spines['top'].set_color('#333')
ax.spines['left'].set_color('#333')
ax.spines['right'].set_color('#333')
ax.tick_params(axis='x', colors='white')
ax.tick_params(axis='y', colors='white')
ax.grid(color='#222', linestyle='--', linewidth=0.5)

plt.title("CORE TRADE AI - LIVE MARKET", color='#00ff9d', fontsize=24, fontweight='bold', pad=20)
plt.tight_layout()

# حفظ الصورة
plt.savefig("dashboard_final.png", facecolor='#050505', dpi=100)
print("Dashboard saved as dashboard_final.png")