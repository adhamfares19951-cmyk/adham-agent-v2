"""Enterprise Autonomous Agency OS Orchestrator.
Coordinates specialized departments across the business:
1. Marketing & Sales (🎯 صيد عملاء وتسويق)
2. Video Studio & Publishing (🎬 استوديو الفيديو والنشر)
3. Software Factory (💻 مصنع البرمجيات)
4. Network & Solar Tech (⚡ هندسة شبكات وطاقة شمسية - Zero Hallucination Enforced)
5. Web & Store Management (🛒 إدارة الموقع والمتجر)
6. Model Intelligence & Smart Routing (🤖 حالة النماذج Ollama / OpenRouter / Gemini)
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from tools.engineering_calculators import (
    calculate_solar_system,
    format_solar_report,
    calculate_subnet_and_mikrotik,
    format_subnet_report,
)
import llm

log = logging.getLogger("agency_orchestrator")


# ==============================================================================
# Department Registry & Contracts
# ==============================================================================

DEPARTMENTS = {
    "marketing_sales": {
        "id": "marketing_sales",
        "title": "صيد عملاء وتسويق",
        "icon": "🎯",
        "description": "استكشاف الأنشطة التجارية في غزة وخانيونس، استخراج أرقام الجوال، تجهيز المعاينات ورسائل عروض شامل POS.",
        "commands": ["/leads", "/pitch", "/crm", "/wa", "/gaza"],
    },
    "video_studio": {
        "id": "video_studio",
        "title": "استوديو الفيديو والنشر",
        "icon": "🎬",
        "description": "صناعة سكريبتات الشورتس، الفيديوهات الطويلة، التعليق الصوتي العصبي، والنشر التلقائي على يوتيوب وتيك توك.",
        "commands": ["/video", "/voice", "/publish_short", "/tiktok", "/yt_upload"],
    },
    "software_factory": {
        "id": "software_factory",
        "title": "مصنع البرمجيات",
        "icon": "💻",
        "description": "فحص وتدقيق المستودعات، الأتمتة البرمجية، كتابة الأكواد والاختبارات الآلية 100% عبر نماذج التكويد المتقدمة.",
        "commands": ["/code", "/repo", "/audit", "/concat", "/skills"],
    },
    "network_solar_tech": {
        "id": "network_solar_tech",
        "title": "هندسة شبكات وطاقة شمسية",
        "icon": "⚡",
        "description": "حسابات الطاقة الشمسية الحتمية (الإنفرتر والبطاريات والألواح)، تقسيم الشبكات، وتوليد إعدادات RouterOS بدون أي هلوسة.",
        "commands": ["/mikrotik", "/server", "/vps"],
        "enforce_deterministic": True,
    },
    "store_web": {
        "id": "store_web",
        "title": "إدارة الموقع والمتجر",
        "icon": "🛒",
        "description": "مراقبة متجر شامل POS، خوادم الاستضافة، تراخيص العملاء، وتوليد فواتير المبيعات وتقارير الإغلاق اليومي.",
        "commands": ["/server", "/license", "/cash", "/tunnel"],
    },
    "model_status": {
        "id": "model_status",
        "title": "حالة النماذج والذكاء الاصطناعي",
        "icon": "🤖",
        "description": "مراقبة توجيه النماذج الهجين (Ollama المحلي، OpenRouter السحابي، وGemini) ومعدلات الاستجابة والتكلفة.",
        "commands": ["/panel"],
    },
}


# ==============================================================================
# Department Execution & Zero-Hallucination Routing
# ==============================================================================

def _extract_numbers(text: str) -> list[float]:
    """Finds all float/int numbers in text."""
    return [float(n.replace(",", "")) for n in re.findall(r"\b\d+(?:\.\d+)?\b", text)]


async def execute_department_task(
    department_id: str,
    query: str,
    params: dict | None = None,
) -> dict[str, Any]:
    """Executes an agency task for a specific department.
    
    CRITICAL ARCHITECTURAL RULE:
    For 'network_solar_tech', deterministic mathematical calculators MUST be used
    directly to guarantee Zero-Hallucination results. LLM is strictly prohibited from
    guessing engineering numbers.
    """
    dept_id = department_id.lower().strip()
    if dept_id not in DEPARTMENTS:
        dept_id = "marketing_sales"

    params = params or {}
    query_str = (query or "").strip()

    # --------------------------------------------------------------------------
    # DEPARTMENT: Network & Solar Tech (Zero-Hallucination Guardrail)
    # --------------------------------------------------------------------------
    if dept_id == "network_solar_tech":
        q_lower = query_str.lower()
        is_solar = any(k in q_lower for k in (
            "solar", "طاقة شمسية", "سولار", "انفرتر", "إنفرتر", "بطارية", "بطاريات", "ألواح", "الواح", "watt", "واط", "أمبير"
        ))
        is_network = any(k in q_lower for k in (
            "mikrotik", "ميكروتك", "routeros", "subnet", "vlan", "cidr", "ip", "شبكة", "تقسيم", "راوتر"
        ))

        if is_solar or ("load_watts" in params):
            # Strict Deterministic Solar Engine Execution
            load = float(params.get("load_watts") or 0)
            hours = float(params.get("backup_hours") or 0)
            voltage = float(params.get("system_voltage") or 24.0)
            panel = float(params.get("panel_wattage") or 400.0)

            # Smart Regex Extraction from query if params are missing
            if load <= 0:
                watt_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:w|watt|واط)", query_str, re.IGNORECASE)
                if watt_match:
                    load = float(watt_match.group(1))
            if hours <= 0:
                hours_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:h|hour|hours|ساعة|ساعات)", query_str, re.IGNORECASE)
                if hours_match:
                    hours = float(hours_match.group(1))
            if not params.get("system_voltage"):
                volt_match = re.search(r"\b(12|24|48)\s*(?:v|volt|فولت)\b", query_str, re.IGNORECASE)
                if volt_match:
                    voltage = float(volt_match.group(1))

            # Fallback to general numbers if regex didn't catch specific units
            if load <= 0 or hours <= 0:
                nums = _extract_numbers(query_str)
                if len(nums) >= 2 and load <= 0 and hours <= 0:
                    load, hours = nums[0], nums[1]
                elif len(nums) >= 1 and load <= 0:
                    load = nums[0]
                    hours = 4.0
                elif len(nums) >= 1 and hours <= 0:
                    hours = nums[0]
                    load = 1000.0
                else:
                    load = 1000.0
                    hours = 4.0

            calc_data = calculate_solar_system(load, hours, voltage, panel)
            report = format_solar_report(calc_data)
            return {
                "department": dept_id,
                "status": "success",
                "engine": "deterministic_solar_calculator",
                "raw_result": calc_data,
                "output": report,
            }

        elif is_network or ("network_cidr" in params):
            # Strict Deterministic Subnetting & Mikrotik Engine Execution
            cidr = params.get("network_cidr") or ""
            count = int(params.get("vlans_count") or 0)

            if not cidr:
                match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}/\d{1,2}\b", query_str)
                if match:
                    cidr = match.group(0)
                else:
                    cidr = "192.168.0.0/24"

            if count <= 0:
                vlan_match = re.search(r"(\d+)\s*(?:vlan|vlans|شبكات|شبكة|أقسام|فروع)", query_str, re.IGNORECASE)
                if vlan_match:
                    count = int(vlan_match.group(1))
                else:
                    # check for words like 'الى 4' or '3 vlans'
                    pre_vlan = re.search(r"(?:إلى|الى|لـ)?\s*(\d+)\s*(?:vlan|vlans|شبكة)", query_str, re.IGNORECASE)
                    if pre_vlan:
                        count = int(pre_vlan.group(1))
                    else:
                        count = 3

            calc_data = calculate_subnet_and_mikrotik(cidr, count)
            report = format_subnet_report(calc_data)
            return {
                "department": dept_id,
                "status": "success",
                "engine": "deterministic_mikrotik_calculator",
                "raw_result": calc_data,
                "output": report,
            }
        else:
            # General network advice: route via OpenRouter with explicit engineering prompt
            system = (
                "أنت كبير مهندسي الشبكات والأنظمة في وكالة أدهم. "
                "أي حسابات طاقة شمسية أو تقسيم شبكات يجب أن تقدمها بأرقام دقيقة وحتمية."
            )
            reply = await llm.generate(system, [{"role": "user", "content": query_str}], task_type="network")
            return {
                "department": dept_id,
                "status": "success",
                "engine": f"smart_router_{reply.provider}",
                "output": reply.text,
            }

    # --------------------------------------------------------------------------
    # DEPARTMENT: Marketing & Sales
    # --------------------------------------------------------------------------
    elif dept_id == "marketing_sales":
        import memory
        from tools import lead_hunter

        q_lower = query_str.lower()
        is_hunt = any(k in q_lower for k in ("صيد", "hunt", "lead", "عملاء", "استخراج", "بحث", "سوبرماركت", "محل", "صيدلية")) or params.get("hunt")

        if is_hunt:
            loc = params.get("location") or "خانيونس"
            query_term = params.get("query") or (query_str if len(query_str) > 3 else "محلات تجارية")
            leads = await lead_hunter.search_and_extract_leads(query=query_term, location=loc, max_results=3)
            if leads:
                lines = [
                    f"🎯 **نتائج صيد العملاء الموثقين ({len(leads)} عملاء - {loc}):**",
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                ]
                for idx, lead in enumerate(leads, 1):
                    # Save to DB if not already
                    memory.add_verified_lead(
                        business_name=lead["business_name"],
                        phone=lead["phone"],
                        source_url=lead["source_url"],
                        proposed_pitch=lead["proposed_pitch"],
                    )
                    # Send telegram alert with wa.me link
                    await lead_hunter.send_lead_to_telegram(lead)
                    b_name_safe = str(lead.get('business_name', '')).replace('*', '')
                    wa_url = lead.get('whatsapp_url') or lead_hunter.format_whatsapp_url(lead['phone'])
                    pitch_prev = str(lead.get('proposed_pitch', ''))[:80].replace('_', ' ').replace('*', '')
                    lines.append(f"*{idx}. {b_name_safe}*")
                    lines.append(f"   📞 جوال: `{lead['phone']}`")
                    lines.append(f"   💬 [محادثة واتساب مباشرة]({wa_url})")
                    lines.append(f"   🔗 [رابط المصدر الموثق]({lead['source_url']})")
                    lines.append(f"   💡 العرض: _{pitch_prev}..._\n")
                lines.append("✅ *تم حفظ العملاء في قاعدة البيانات وإرسال التنبيهات المباشرة إلى التيليجرام.*")
                output = "\n".join(lines)
            else:
                output = f"🔍 تم فحص الأنشطة في {loc} لبحث '{query_term}'. يمكنك استعراض العملاء الموثقين المحفوظين عبر زر 'العملاء الموثقين'."
            return {"department": dept_id, "status": "success", "output": output}

        leads_count = 0
        verified_count = 0
        try:
            with memory._db() as c:
                row = c.execute("SELECT COUNT(*) FROM leads").fetchone()
                leads_count = row[0] if row else 0
                row2 = c.execute("SELECT COUNT(*) FROM verified_leads").fetchone()
                verified_count = row2[0] if row2 else 0
        except Exception:
            pass

        output = (
            f"🎯 **قسم صيد العملاء والتسويق (Marketing & Sales Department):**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 إجمالي العملاء في النظام: `{leads_count}` | الموثقين بأرقام مؤكدة: `{verified_count}` عميل.\n\n"
            f"🚀 **المهام التشغيلية المتاحة:**\n"
            f"• استخراج الأنشطة التجارية الحقيقية: أزرار الصيد أدناه أو `/leads`\n"
            f"• تجهيز رسالة بيع ومعاينة: `/pitch [رقم النشاط]`\n"
            f"• إدارة العملاء المحتملين: `/crm`\n"
            f"• إرسال وتواصل واتساب: `/wa [رقم الجوال]`\n"
        )
        return {"department": dept_id, "status": "success", "output": output}

    # --------------------------------------------------------------------------
    # DEPARTMENT: Video Studio
    # --------------------------------------------------------------------------
    elif dept_id == "video_studio":
        from tools import social_studio
        q_lower = query_str.lower()
        is_gen = any(k in q_lower for k in ("سكريبت", "فيديو", "ريلز", "script", "video", "صوت", "شورتس", "voice", "توليد")) or params.get("generate")

        if is_gen:
            topic = params.get("topic") or "pos"
            if any(k in q_lower for k in ("تداول", "trading", "mql", "فوركس")):
                topic = "trading"
            elif any(k in q_lower for k in ("طاقة", "شبك", "solar", "mikrotik", "سولار")):
                topic = "network_solar"

            script_data = social_studio.create_social_script(topic)
            await social_studio.send_script_approval_preview(script_data, script_data["queue_id"])

            output = (
                f"🎬 **تم توليد سكريبت فيديو جديد بنجاح!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📌 **العنوان:** {script_data['title']}\n"
                f"🎯 **الموضوع:** `{script_data['topic']}`\n"
                f"🪝 **الهوك:** _{script_data['hook']}_\n"
                f"🔢 **رقم الطابور:** `#{script_data['queue_id']}`\n\n"
                f"✅ *تم إرسال بطاقة المعاينة وأزرار الاعتماد وتوليد التعليق الصوتي إلى التيليجرام مباشرة.*"
            )
            return {"department": dept_id, "status": "success", "output": output}

        output = (
            "🎬 **استوديو الفيديو والنشر التلقائي (Video & Motion Studio):**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎥 إنتاج فيديوهات ريلز وشورتس 9:16 فورياً:\n"
            "• اضغط أدناه لتوليد سكريبت ترويجي معتمد فوراً (POS / تداول / شبكات).\n"
            "• `/video [عنوان الفيديو | الهوك الجذاب | النص التفصيلي]`\n"
            "• `/voice [نص للتعليق الصوتي العصبي العربي]`\n"
            "• `/publish_short [مسار الفيديو | عنوان | وصف | وسوم]`\n"
        )
        return {"department": dept_id, "status": "success", "output": output}

    # --------------------------------------------------------------------------
    # DEPARTMENT: Software Factory
    # --------------------------------------------------------------------------
    elif dept_id == "software_factory":
        output = (
            "💻 **مصنع البرمجيات والهندسة المعمارية (Software Factory):**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🛠️ الأدوات البرمجية المؤتمتة:\n"
            "• التحديث الشامل لمشاريعك واختباراتها: `/code update` أو `/code test`\n"
            "• فحص وتنزيل أي مستودع GitHub: `/repo [url]`\n"
            "• تدقيق وفحص ثغرات المشروع: `/audit [project_dir]`\n"
            "• تجميع وفهرسة كود أي مشروع للذكاء الاصطناعي: `/concat [folder]`\n"
            "• استدعاء مهارات البرمجة (480 مهارة): `/skills [query]`\n"
        )
        return {"department": dept_id, "status": "success", "output": output}

    # --------------------------------------------------------------------------
    # DEPARTMENT: Store & Web Management
    # --------------------------------------------------------------------------
    elif dept_id == "store_web":
        import memory
        prods = memory.list_products(active_only=True)
        new_orders = memory.list_client_orders(status="new")
        all_orders = memory.list_client_orders()

        from core.tunnel_manager import get_tunnel_manager
        tm = get_tunnel_manager()
        pub_url = tm.get_public_url()
        tunnel_display = f"[{pub_url}]({pub_url}) 🟢 (نشط عبر HTTPS)" if pub_url else "`غير متصل حالياً (اضغط زر تشغيل النفق بالأسفل)` ⚪"

        output = (
            "🛒 **إدارة الموقع والمتجر (Web Platform & Store Management):**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 **المنتجات والخدمات المعروضة بالموقع:** `{len(prods)}` منتج/خدمة نشطة.\n"
            f"📥 **طلبات العملاء الجديدة غير المعالجة:** `{len(new_orders)}` طلب جديد.\n"
            f"📊 **إجمالي الطلبات المستلمة:** `{len(all_orders)}` طلب.\n"
            f"🌐 **الرابط الخارجي العام (Public URL):**\n   {tunnel_display}\n"
            f"📡 **المنفذ المحلي:** `http://127.0.0.1:8080`\n\n"
            "🛠️ **الأدوات التشغيلية المتاحة:**\n"
            "• استعراض كافة منتجات المتجر وتعديلها فوراً\n"
            "• مراجعة طلبات الشراء الواردة من العملاء\n"
            "• تشغيل وتحديث نفق Cloudflare الخارجي\n"
            "• توليد رخص شامل POS للمحلات: `/license [client] [days]`\n"
        )
        return {"department": dept_id, "status": "success", "output": output}

    # --------------------------------------------------------------------------
    # DEPARTMENT: Model Status
    # --------------------------------------------------------------------------
    elif dept_id == "model_status":
        status = await llm.check_models_status()
        active_llm = llm.get_llm()
        output = (
            "🤖 **لوحة حالة نماذج الذكاء الاصطناعي (Hybrid Smart Routing):**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👑 **المزود الرئيسي النشط:** `{active_llm.main_name}`\n\n"
            f"• **Ollama (المحلي / الاقتصادي للتلخيص والفرز):**\n"
            f"   - الحالة: {status['ollama']['status']}\n"
            f"   - الموديل: `{status['ollama']['model']}`\n"
            f"   - الرابط: `{status['ollama']['endpoint']}`\n\n"
            f"• **OpenRouter (السحابي للمهام المعقدة والشبكات):**\n"
            f"   - الحالة: {status['openrouter']['status']}\n"
            f"   - الموديل: `{status['openrouter']['model']}`\n\n"
            f"• **Gemini (النموذج القياسي لاستدعاء الأدوات):**\n"
            f"   - الحالة: {status['gemini']['status']}\n"
            f"   - الموديل: `{status['gemini']['model']}`\n\n"
            f"🔄 *النظام يقوم بالتبديل التلقائي الذكي والـ Fallback في حال تعطل أي مزود.*"
        )
        return {"department": dept_id, "status": "success", "raw_result": status, "output": output}

    return {"department": dept_id, "status": "unknown_department", "output": "القسم غير معرف."}


def get_departments_summary() -> list[dict[str, Any]]:
    """Returns a list of all department cards."""
    return list(DEPARTMENTS.values())
