$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'powershell' }
$rid = 275508658
# Step 1: set tag_name and name
$body1 = @{ tag_name = 'v0.1.5'; name = 'v0.1.5' } | ConvertTo-Json
Invoke-RestMethod -Uri ("https://api.github.com/repos/zava78/ha-osservaprezzi-carburanti/releases/" + $rid) -Method Patch -Headers $headers -Body $body1 -ContentType 'application/json'
Write-Output "Patched tag_name and name"
# Step 2: set draft = false
$body2 = @{ draft = $false } | ConvertTo-Json
Invoke-RestMethod -Uri ("https://api.github.com/repos/zava78/ha-osservaprezzi-carburanti/releases/" + $rid) -Method Patch -Headers $headers -Body $body2 -ContentType 'application/json'
Write-Output "Set draft=false"
# Step 3: update body (changelog in italiano)
$body3 = @{ body = "v0.1.5 — Changelog (italiano)\n\n- Aggiunto link al sito del Ministero per la ricerca degli impianti: https://carburanti.mise.gov.it/ospzSearch/zona\n- Config Flow: quando si aggiunge una singola stazione, il titolo della Config Entry prende automaticamente il campo 'company' (se presente).\n- Aggiunte/aggiornate traduzioni italiane per i passaggi di configurazione.\n- Pulita la storia del repository per rimuovere accidentalmente un token esposto; il token è stato revocato." } | ConvertTo-Json
Invoke-RestMethod -Uri ("https://api.github.com/repos/zava78/ha-osservaprezzi-carburanti/releases/" + $rid) -Method Patch -Headers $headers -Body $body3 -ContentType 'application/json'
Write-Output "Updated release body"
