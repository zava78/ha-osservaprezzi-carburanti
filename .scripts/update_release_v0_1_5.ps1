$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'powershell' }
$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/zava78/ha-osservaprezzi-carburanti/releases/tags/v0.1.5' -Headers $headers
Write-Output "Found release id: $($release.id)"
$body = @{ body = 'Release v0.1.5: history cleaned to remove an accidentally committed token. The token was revoked. If you cloned previously, re-clone or run `git fetch --all && git reset --hard origin/main`.' } | ConvertTo-Json
Invoke-RestMethod -Uri ("https://api.github.com/repos/zava78/ha-osservaprezzi-carburanti/releases/" + $release.id) -Method Patch -Headers $headers -Body $body -ContentType 'application/json'
Write-Output "Release updated"
