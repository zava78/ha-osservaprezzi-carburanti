$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'powershell' }
# Release id trovato precedentemente: 275508658
$rid = 275508658
$body = @{ 
    tag_name   = 'v0.1.5'
    name       = 'v0.1.5'
    draft      = $false
    prerelease = $false
    body       = @"
v0.1.5 — Changelog (italiano)

- Aggiunto link al sito del Ministero per la ricerca degli impianti: https://carburanti.mise.gov.it/ospzSearch/zona
- Config Flow: quando si aggiunge una singola stazione, il titolo della Config Entry prende automaticamente il campo `company` (se presente).
- Aggiunte/aggiornate traduzioni italiane per i passaggi di configurazione.
- Pulita la storia del repository per rimuovere accidentalmente un token esposto; il token è stato revocato.

Se avevi clonato il repository prima della pulizia, esegui: `git fetch --all && git reset --hard origin/main` oppure riclona il repository.
"@ 
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri ("https://api.github.com/repos/zava78/ha-osservaprezzi-carburanti/releases/" + $rid) -Method Patch -Headers $headers -Body $body -ContentType 'application/json'
Write-Output "Release v0.1.5 finalizzata (draft=false) e descrizione aggiornata."