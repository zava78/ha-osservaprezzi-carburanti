$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'powershell' }
$rid = 275508658
$body = @{ body = 'Release v0.1.5: history cleaned to remove an accidentally committed token. The token was revoked. If you cloned previously, re-clone or run `git fetch --all && git reset --hard origin/main`.' } | ConvertTo-Json
Invoke-RestMethod -Uri ("https://api.github.com/repos/zava78/ha-osservaprezzi-carburanti/releases/" + $rid) -Method Patch -Headers $headers -Body $body -ContentType 'application/json'
Write-Output "Patched release $rid"
