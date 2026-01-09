import os
import json
import urllib.request

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print('GITHUB_TOKEN not set in environment')
    raise SystemExit(1)

rid = 275508658
url = f'https://api.github.com/repos/zava78/ha-osservaprezzi-carburanti/releases/{rid}'
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'User-Agent': 'python'
}

payload = {
    'tag_name': 'v0.1.5',
    'name': 'v0.1.5',
    'draft': False,
    'prerelease': False,
    'body': (
        "v0.1.5 — Changelog (italiano)\n\n"
        "- Aggiunto link al sito del Ministero per la ricerca degli impianti: https://carburanti.mise.gov.it/ospzSearch/zona\n"
        "- Config Flow: quando si aggiunge una singola stazione, il titolo della Config Entry prende automaticamente il campo 'company' (se presente).\n"
        "- Aggiunte/aggiornate traduzioni italiane per i passaggi di configurazione.\n"
        "- Pulita la storia del repository per rimuovere accidentalmente un token esposto; il token è stato revocato.\n\n"
        "Se avevi clonato il repository prima della pulizia, esegui: `git fetch --all && git reset --hard origin/main` oppure riclona il repository."
    )
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={**headers, 'Content-Type': 'application/json'}, method='PATCH')
with urllib.request.urlopen(req) as resp:
    body = resp.read().decode('utf-8')
    print('Response:', resp.status)
    print(body)
