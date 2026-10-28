import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(r'C:\Projects\adham-agent\tools\proposal_pdf_builder.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('async def _handle_generate_proposal')
if idx != -1:
    print(text[idx+500:idx+1500])
