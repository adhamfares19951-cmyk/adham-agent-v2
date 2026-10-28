import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Projects\adham-agent\tools\proposal_pdf_builder.py', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length of proposal_pdf_builder.py:", len(text))
for line in text.splitlines()[:60]:
    print(line)
