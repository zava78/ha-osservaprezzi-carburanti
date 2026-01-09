# Script per creare tag v0.1.2 e pubblicare la release (non-interattivo)
$ErrorActionPreference = 'Stop'
$repoPath = 'Z:\AAA cose varie boh\ha-carbutanti-ita'
Set-Location $repoPath

if (-not $env:GITHUB_TOKEN) {
  Write-Error "GITHUB_TOKEN non è impostato. Imposta la variabile d'ambiente e riprova."
  exit 1
}

Write-Output "Working directory: $(Get-Location)"

# Aggiorna main
git checkout main
git pull origin main

# Commit eventuali cambi
$changes = git status --porcelain
if ($changes -ne '') {
  Write-Output "Modifiche locali rilevate; commit in corso..."
  git add -A
  git commit -m "Fix: Config Flow, manifest; prepare v0.1.2 release"
  git push origin main
} else {
  Write-Output "Nessuna modifica da committare."
}

# Crea tag se non esiste
$tag = 'v0.1.2'
$tagExists = $false
try {
  git rev-parse --verify $tag 2>$null | Out-Null
  $tagExists = $true
} catch {
  $tagExists = $false
}

if ($tagExists) {
  Write-Output "Tag $tag già presente localmente."
} else {
  Write-Output "Creazione tag $tag..."
  git tag -a $tag -m "Release $tag"
  git push origin $tag
}

# Verifica se la release esiste su GitHub
$owner = 'zava78'
$repo = 'ha-osservaprezzi-carburanti'
$releaseUri = "https://api.github.com/repos/$owner/$repo/releases/tags/$tag"
$headers = @{ Authorization = "token $env:GITHUB_TOKEN"; 'User-Agent' = 'powershell' }

$releaseExists = $false
try {
  $rel = Invoke-RestMethod -Method Get -Uri $releaseUri -Headers $headers -ErrorAction Stop
  Write-Output "Release esistente: $($rel.html_url)"
  $releaseExists = $true
} catch {
  # Se 404, creiamo la release
  $resp = $_.Exception.Response
  if ($resp -and $resp.StatusCode -eq 404) {
    Write-Output "Release non trovata. Procedo alla creazione..."
    $body = @{ tag_name = $tag; target_commitish = 'main'; name = $tag; body = "Rilascio ${tag}: correzione del Config Flow, rimozione del shim locale e aggiornamenti alle traduzioni italiane."; draft = $false; prerelease = $false }
    $json = $body | ConvertTo-Json -Depth 6
    try {
      $created = Invoke-RestMethod -Method Post -Uri "https://api.github.com/repos/$owner/$repo/releases" -Headers $headers -Body $json -ContentType 'application/json' -ErrorAction Stop
      Write-Output "Release creata: $($created.html_url)"
      $releaseExists = $true
    } catch {
      Write-Error "Fallita creazione release: $($_.Exception.Message)"
      if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $respBody = $reader.ReadToEnd()
        Write-Error "Response body: $respBody"
      }
      exit 1
    }
  } else {
    Write-Error "Errore nel controllare la release: $($_.Exception.Message)"
    if ($_.Exception.Response) {
      $stream = $_.Exception.Response.GetResponseStream()
      $reader = New-Object System.IO.StreamReader($stream)
      $respBody = $reader.ReadToEnd()
      Write-Error "Response body: $respBody"
    }
    exit 1
  }
}

Write-Output "Operazione completata."
