import re
from pathlib import Path

log_file = Path(r"C:\Users\Administrator\AppData\Local\Google\Chrome\User Data\Default\Local Extension Settings\omghfjlpggmjjaagoclmmobgdodcjboh\000003.log")
content = log_file.read_bytes()

# Find country settings
country_matches = re.findall(b'(\"[a-zA-Z0-9_-]{2,30}\":\s*\"[a-zA-Z0-9_.-]+\")', content)
for cm in country_matches:
    decoded = cm.decode(errors="ignore")
    if any(k in decoded.lower() for k in ["country", "state", "status", "enabled", "selected", "current", "location"]):
        print("Match:", decoded)

# Find json blocks
json_blocks = re.findall(b'\{[^{}]{10,200}\}', content)
for jb in json_blocks:
    d = jb.decode(errors="ignore")
    if "country" in d.lower() or "us" in d.lower() or "active" in d.lower():
        print("JSON:", d)
