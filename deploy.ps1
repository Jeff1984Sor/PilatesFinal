# Sobe o Mayris Pilates para a VPS: confere o git daqui e roda deploy/deploy.sh no servidor.
# Uso (PowerShell, na pasta PilatesFinal):  .\deploy.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$sujo = git status --porcelain --untracked-files=no | Where-Object { $_ -notmatch "__pycache__|\.pyc$" }
if ($sujo) {
    Write-Host "Ha alteracoes sem commit. Faca commit e push antes de subir:" -ForegroundColor Yellow
    $sujo
    exit 1
}
git fetch origin --quiet
$local  = git rev-parse HEAD
$remoto = git rev-parse origin/main
if ($local -ne $remoto) {
    Write-Host "O seu commit local nao esta no GitHub. Rode 'git push' primeiro." -ForegroundColor Yellow
    exit 1
}

Write-Host "Subindo $(git rev-parse --short HEAD) para o servidor..." -ForegroundColor Cyan
# 'flicsales' e o apelido da VPS em ~/.ssh/config (usuario deploy)
ssh flicsales "bash ~/pilates/deploy/deploy.sh"
