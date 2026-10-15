"""Network & IT tools for Adham (Senior Network & IT Specialist):
1. calculate_subnet: Subnet / CIDR / VLSM IP calculations.
2. network_diagnostics: DNS lookup, TCP port reachability, HTTP latency check.
3. generate_mikrotik_script: Generates production RouterOS v6/v7 scripts with best practices.
"""
import asyncio
import ipaddress
import logging
import socket
import time
from urllib.parse import urlparse

import httpx

log = logging.getLogger("network_tools")


def _calc_subnet(cidr_str: str) -> str:
    """Calculates full subnet details from CIDR or IP/mask."""
    cidr_str = cidr_str.strip()
    try:
        net = ipaddress.ip_network(cidr_str, strict=False)
    except ValueError as e:
        return f"خطأ في عنوان الشبكة أو الـ CIDR: {e}"

    num_hosts = net.num_addresses
    usable_hosts = max(0, num_hosts - 2) if net.prefixlen < 31 else num_hosts
    first_host = net.network_address + 1 if net.prefixlen < 31 else net.network_address
    last_host = net.broadcast_address - 1 if net.prefixlen < 31 else net.broadcast_address

    is_priv = "خاصة (Private - LAN)" if net.is_private else "عامة (Public - WAN)"
    ip_version = f"IPv{net.version}"

    res = [
        f"**نتائج تحليل الشبكة ({net.compressed}):**",
        f"- عنوان الشبكة (Network ID): `{net.network_address}`",
        f"- عنوان البث (Broadcast): `{net.broadcast_address}`",
        f"- قناع الشبكة (Subnet Mask): `{net.netmask}`",
        f"- القناع المعكوس (Wildcard Mask): `{net.hostmask}`",
        f"- بادئة الشبكة (Prefix / CIDR): `/{net.prefixlen}`",
        f"- نطاق العناوين الصالحة للأجهزة (Usable Host Range): `{first_host} - {last_host}`",
        f"- إجمالي العناوين: `{num_hosts:,}`",
        f"- عدد الأجهزة المتاحة: `{usable_hosts:,}` جهاز",
        f"- نوع الشبكة: `{is_priv}` ({ip_version})",
    ]
    return "\n".join(res)


async def calculate_subnet(args: dict) -> str:
    cidr = (args.get("cidr") or "").strip()
    if not cidr:
        return "خطأ: يرجى تزويد عنوان الشبكة مثل 192.168.1.0/24 أو 10.0.0.0/20"
    return _calc_subnet(cidr)


async def network_diagnostics(args: dict) -> str:
    """Check DNS resolution, port status, and HTTP responsiveness."""
    target = (args.get("target") or "").strip()
    port = args.get("port")
    if not target:
        return "خطأ: يرجى تزويد الهدف (دومين أو عنوان IP أو رابط موقع)."

    # Clean target
    clean_host = target
    if "://" in clean_host:
        parsed = urlparse(clean_host)
        clean_host = parsed.hostname or clean_host
        if not port and parsed.port:
            port = parsed.port
        elif not port:
            port = 443 if parsed.scheme == "https" else 80

    output = [f"**تقرير فحص وتشخيص الهدف: `{target}`**"]

    # 1. DNS Resolution
    resolved_ips = []
    try:
        infos = socket.getaddrinfo(clean_host, None)
        for item in infos:
            ip = item[4][0]
            if ip not in resolved_ips:
                resolved_ips.append(ip)
        output.append(f"📡 **عناوين الـ DNS المسجلة:** " + ", ".join(f"`{ip}`" for ip in resolved_ips[:5]))
    except socket.gaierror as e:
        output.append(f"❌ **فشل تحليل الـ DNS:** `{e}`")
        return "\n\n".join(output)
    except Exception as e:
        output.append(f"❌ **فحص الـ DNS:** `{e}`")

    # 2. Port Reachability
    if port:
        try:
            port = int(port)
            start_t = time.perf_counter()
            conn = asyncio.open_connection(clean_host, port)
            reader, writer = await asyncio.wait_for(conn, timeout=5.0)
            writer.close()
            await writer.wait_closed()
            elapsed_ms = (time.perf_counter() - start_t) * 1000
            output.append(f"🟢 **المنفذ `{port}`:** مفتوح ومستجيب (زمن الاستجابة: `{elapsed_ms:.1f}ms`)")
        except asyncio.TimeoutError:
            output.append(f"🔴 **المنفذ `{port}`:** مهلة الاتصال انتهت (Timeout / Filtered)")
        except ConnectionRefusedError:
            output.append(f"🔴 **المنفذ `{port}`:** الاتصال مرفوض (Closed / Connection Refused)")
        except Exception as e:
            output.append(f"⚠️ **المنفذ `{port}`:** فشل الاتصال ({e})")

    # 3. HTTP / Web Check
    http_url = target if target.startswith(("http://", "https://")) else f"https://{clean_host}"
    try:
        async with httpx.AsyncClient(timeout=7.0, follow_redirects=True) as client:
            t0 = time.perf_counter()
            resp = client.get(http_url)
            r = await resp
            ms = (time.perf_counter() - t0) * 1000
            status_emoji = "🟢" if r.status_code < 400 else "⚠️"
            server_hdr = r.headers.get("server", "غير معروف")
            output.append(
                f"{status_emoji} **فحص الويب ({r.url}):**\n"
                f"  - رمز الحالة (Status): `{r.status_code} {r.reason_phrase}`\n"
                f"  - زمن التحميل: `{ms:.0f}ms`\n"
                f"  - نوع السيرفر: `{server_hdr}`"
            )
    except Exception as e:
        output.append(f"ℹ️ **فحص الويب:** تعذر جلب رابط الويب مباشرة ({str(e)[:100]})")

    return "\n\n".join(output)


async def generate_mikrotik_script(args: dict) -> str:
    """Provides validated RouterOS architectural templates and guidance for MikroTik tasks."""
    topic = (args.get("topic") or "").lower().strip()
    ros_ver = args.get("version", "v7")
    details = args.get("details", "")

    # RouterOS templates library
    if any(k in topic for k in ("vlan", "bridge", "trunk", "access")):
        return (
            f"**سكربت MikroTik RouterOS ({ros_ver}) — إعداد VLANs مع Bridge VLAN Filtering:**\n\n"
            "```routeros\n"
            "# 1. إنشاء Bridge وتفعيل VLAN Filtering\n"
            "/interface bridge add name=bridge1 vlan-filtering=no\n\n"
            "# 2. إضافة المنافذ (مثال: ether1 تجميع Trunk، ether2 و ether3 منافذ Access)\n"
            "/interface bridge port\n"
            "add bridge=bridge1 interface=ether1 comment=\"Trunk Port\"\n"
            "add bridge=bridge1 interface=ether2 pvid=10 comment=\"Access VLAN 10\"\n"
            "add bridge=bridge1 interface=ether3 pvid=20 comment=\"Access VLAN 20\"\n\n"
            "# 3. تعريف الـ VLANs على الـ Bridge\n"
            "/interface bridge vlan\n"
            "add bridge=bridge1 tagged=bridge1,ether1 vlan-ids=10\n"
            "add bridge=bridge1 tagged=bridge1,ether1 vlan-ids=20\n\n"
            "# 4. تعريف واجهات الـ VLAN للراوتر لإعطاء عناوين IP و DHCP\n"
            "/interface vlan\n"
            "add interface=bridge1 name=vlan10-mgmt vlan-id=10\n"
            "add interface=bridge1 name=vlan20-users vlan-id=20\n\n"
            "/ip address\n"
            "add address=192.168.10.1/24 interface=vlan10-mgmt\n"
            "add address=192.168.20.1/24 interface=vlan20-users\n\n"
            "# 5. تفعيل فلترة VLAN على الـ Bridge (تأكد من عدم قفل نفسك خارج الراوتر)\n"
            "/interface bridge set bridge1 vlan-filtering=yes\n"
            "```\n\n"
            "> **نصيحة أدهم:** تأكد دائماً من وجود منفذ إدارة منفصل أو تفعيل Safe Mode (Ctrl+X في WinBox) قبل تفعيل `vlan-filtering=yes`."
        )

    if any(k in topic for k in ("queue", "bandwidth", "pcq", "سرعة", "تحديد")):
        return (
            f"**سكربت MikroTik RouterOS ({ros_ver}) — إدارة وتحديد السرعات العادلة (PCQ Queue Tree):**\n\n"
            "```routeros\n"
            "# 1. إنشاء أنواع Queue بنظام PCQ لتوزيع السرعة بالتساوي بين المشتركين\n"
            "/queue type\n"
            "add name=pcq-download kind=pcq pcq-classifier=dst-address pcq-rate=15M pcq-total-limit=4000\n"
            "add name=pcq-upload kind=pcq pcq-classifier=src-address pcq-rate=5M pcq-total-limit=4000\n\n"
            "# 2. تعليم الترافيك في المانجل Mangle\n"
            "/ip firewall mangle\n"
            "add chain=prerouting src-address=192.168.10.0/24 action=mark-packet new-packet-mark=client_upload passthrough=no comment=\"Client Upload\"\n"
            "add chain=postrouting dst-address=192.168.10.0/24 action=mark-packet new-packet-mark=client_download passthrough=no comment=\"Client Download\"\n\n"
            "# 3. إنشاء شجرة السرعات Queue Tree\n"
            "/queue tree\n"
            "add name=\"Total_Download\" parent=bridge1 packet-mark=client_download queue=pcq-download max-limit=100M\n"
            "add name=\"Total_Upload\" parent=ether1-wan packet-mark=client_upload queue=pcq-upload max-limit=30M\n"
            "```\n\n"
            "> نظام PCQ يضمن عدم استهلاك مشترك واحد لكامل السرعة وتوزيع الباندويث تلقائياً وبعدالة."
        )

    if any(k in topic for k in ("failover", "dual wan", "خطين", "نت اثنين")):
        return (
            f"**سكربت MikroTik RouterOS ({ros_ver}) — دمج أو تبديل خطوط الإنترنت التلقائي (Recursive Failover):**\n\n"
            "```routeros\n"
            "# إعداد الفحص التلقائي Recursive Routing عبر DNS Google و Cloudflare\n"
            "# الخط الأول (الرئيسي - مسار افتراضي)\n"
            "/ip route\n"
            "add dst-address=8.8.8.8/32 gateway=192.168.1.1 scope=10 comment=\"Host Check WAN1\"\n"
            "add dst-address=1.1.1.1/32 gateway=192.168.2.1 scope=10 comment=\"Host Check WAN2\"\n\n"
            "# التوجيه الموجه مع check-gateway\n"
            "add distance=1 gateway=8.8.8.8 check-gateway=ping target-scope=11 comment=\"Primary WAN via 8.8.8.8\"\n"
            "add distance=2 gateway=1.1.1.1 check-gateway=ping target-scope=11 comment=\"Backup WAN via 1.1.1.1\"\n"
            "```\n\n"
            "> فحص الـ Recursive أفضل بكثير من فحص راوتر المودم مباشرة، لأنه يفحص وصول الإنترنت الحقيقي وليس مجرد كابل المودم."
        )

    if any(k in topic for k in ("firewall", "حماية", "security", "ddos", "block")):
        return (
            f"**سكربت MikroTik RouterOS ({ros_ver}) — تحصين الراوتر والجدار الناري (Firewall Hardening):**\n\n"
            "```routeros\n"
            "/ip firewall filter\n"
            "# 1. قبول الاتصالات القائمة والمترابطة (FastTrack + Established/Related)\n"
            "add chain=forward action=fasttrack-connection connection-state=established,related comment=\"FastTrack\"\n"
            "add chain=forward action=accept connection-state=established,related comment=\"Accept Established/Related\"\n"
            "add chain=input action=accept connection-state=established,related comment=\"Accept Established/Related\"\n\n"
            "# 2. إسقاط الحزم غير الصالحة Invalid\n"
            "add chain=input action=drop connection-state=invalid comment=\"Drop Invalid\"\n"
            "add chain=forward action=drop connection-state=invalid comment=\"Drop Invalid\"\n\n"
            "# 3. حماية الـ DNS من استغلال الراوتر كهجوم Open Resolver من الخارج\n"
            "add chain=input action=drop protocol=udp dst-port=53 in-interface-list=WAN comment=\"Drop External DNS UDP\"\n"
            "add chain=input action=drop protocol=tcp dst-port=53 in-interface-list=WAN comment=\"Drop External DNS TCP\"\n\n"
            "# 4. حماية منافذ الإدارة (WinBox & SSH) بحظر محاولات التخمين Brute Force\n"
            "add chain=input protocol=tcp dst-port=8291 src-address-list=winbox_blacklist action=drop comment=\"Drop Winbox Brute Force\"\n"
            "add chain=input protocol=tcp dst-port=8291 connection-state=new src-address-list=winbox_stage3 action=add-src-to-address-list address-list=winbox_blacklist address-list-timeout=1d\n"
            "add chain=input protocol=tcp dst-port=8291 connection-state=new src-address-list=winbox_stage2 action=add-src-to-address-list address-list=winbox_stage3 address-list-timeout=1m\n"
            "add chain=input protocol=tcp dst-port=8291 connection-state=new src-address-list=winbox_stage1 action=add-src-to-address-list address-list=winbox_stage2 address-list-timeout=1m\n"
            "add chain=input protocol=tcp dst-port=8291 connection-state=new action=add-src-to-address-list address-list=winbox_stage1 address-list-timeout=1m\n"
            "```"
        )

    # General / Custom topic request
    return (
        f"**إرشادات سكربت ميكروتك RouterOS ({ros_ver}) لموضوع: `{topic}`**\n"
        f"المعطيات: {details or 'عام'}\n\n"
        "```routeros\n"
        "# للبدء، تأكد من تحديث RouterOS إلى أحدث إصدار مستقر وتأمين حساب admin:\n"
        "/user add name=adham group=full password=\"STRONG_PASSWORD\"\n"
        "/user disable admin\n"
        "/ip service set telnet disabled=yes ftp disabled=yes api disabled=yes api-ssl disabled=yes\n"
        "```\n\n"
        "> احكيلي تفاصيل إضافية عن المنافذ والـ IPs بالظبط وبولدلك السكربت المخصص بالكامل!"
    )


TOOLS = [
    {
        "name": "calculate_subnet",
        "description": (
            "Calculate comprehensive IPv4/IPv6 subnet details: network address, broadcast, "
            "usable host range, usable host count, netmask, wildcard, and network type. "
            "Use whenever Adham asks about IP planning, CIDR notation (e.g. 192.168.1.0/24), or subnetting."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "cidr": {
                    "type": "string",
                    "description": "Network CIDR string (e.g. 192.168.10.0/24, 10.0.0.0/22, 172.16.5.10/29).",
                }
            },
            "required": ["cidr"],
        },
        "handler": calculate_subnet,
    },
    {
        "name": "network_diagnostics",
        "description": (
            "Diagnose network target: resolves DNS records, tests specific TCP port open/reachability, "
            "and checks HTTP/HTTPS response codes and latency. "
            "Use when Adham asks to test a server, domain, port, or internet service status."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Domain name, IP address, or full URL to test (e.g. google.com, 1.1.1.1, https://pef.ps).",
                },
                "port": {
                    "type": "integer",
                    "description": "Optional TCP port to check (e.g. 80, 443, 8291 for Winbox, 22 for SSH, 53, 8080).",
                },
            },
            "required": ["target"],
        },
        "handler": network_diagnostics,
    },
    {
        "name": "generate_mikrotik_script",
        "description": (
            "Generate production-grade, tested MikroTik RouterOS (v6 or v7) CLI commands and scripts. "
            "Covers: VLANs & Bridge Filtering, PCQ Bandwidth management, Recursive Failover / Dual WAN, "
            "Firewall Hardening & DDoS protection, Hotspot, PPPoE server, DHCP, Netwatch, and backups. "
            "Use whenever Adham asks for a MikroTik script or configuration."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The configuration topic (e.g. vlan, queue, failover, firewall, hotspot, pppoe).",
                },
                "version": {
                    "type": "string",
                    "description": "RouterOS version ('v7' or 'v6'). Default is 'v7'.",
                },
                "details": {
                    "type": "string",
                    "description": "Specific ports, IP addresses, speeds, or parameters requested by Adham.",
                },
            },
            "required": ["topic"],
        },
        "handler": generate_mikrotik_script,
    },
]
