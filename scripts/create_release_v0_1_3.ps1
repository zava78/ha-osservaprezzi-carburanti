# Script per creare/pushare tag v0.1.3 e creare la release v0.1.3 (non-interattivo)
# Uso: impostare $env:GITHUB_TOKEN in questa sessione o come variabile d'ambiente utente prima di eseguire.
$ErrorActionPreference = 'Stop'

if (-not $env:GITHUB_TOKEN) {
    Write-Error "GITHUB_TOKEN non è impostato. Imposta l'ambiente e riprova."
    exit 1
}

$repoPath = 'Z:\AAA cose varie boh\ha-carbutanti-ita'
Set-Location $repoPath

git checkout main
git pull origin main

$tag = 'v0.1.3'
$owner = 'zava78'
$repo = 'ha-osservaprezzi-carburanti'

# Controllo tag remoto/local
$remoteInfo = git ls-remote --tags origin refs/tags/$tag
try { git rev-parse --verify $tag > $null; $localExists = $true } catch { $localExists = $false }
$remoteExists = -not [string]::IsNullOrEmpty($remoteInfo)

if (-not $localExists) {
    Write-Output "Creazione tag $tag localmente..."
    git tag -a $tag -m "Release $tag"
}
if (-not $remoteExists) {
    Write-Output "Push del tag $tag su origin..."
    git push origin $tag
}
else {
    Write-Output "Tag $tag già presente su remoto."
}

# Creazione release via API
$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'powershell' }
$releaseUri = "https://api.github.com/repos/$owner/$repo/releases/tags/$tag"
try {
    $existing = Invoke-RestMethod -Method Get -Uri $releaseUri -Headers $headers -ErrorAction Stop
    Write-Output "Release $tag già presente: $($existing.html_url)"
    exit 0
}
catch {
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode -ne 404) {
        Write-Error "Errore controllando la release: $($_.Exception.Message)"
        exit 1
    }
    Write-Output "Release non trovata: la creo ora..."
}

$message = "Rilascio ${tag}: Correzione parsing file traduzioni (it.json) e fix minori nelle traduzioni."
$body = @{ tag_name = $tag; target_commitish = 'main'; name = $tag; body = $message; draft = $false; prerelease = $false }
$json = $body | ConvertTo-Json -Depth 6

try {
    $created = Invoke-RestMethod -Method Post -Uri "https://api.github.com/repos/$owner/$repo/releases" -Headers $headers -Body $json -ContentType 'application/json' -ErrorAction Stop
    Write-Output "Release creata: $($created.html_url)"
}
catch {
    Write-Error "Fallita creazione release: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $sr = $_.Exception.Response.GetResponseStream(); $r = New-Object System.IO.StreamReader($sr); $rb = $r.ReadToEnd(); Write-Error "Response body: $rb" 
    }
    exit 1
}
