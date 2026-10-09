#!/usr/bin/env bash
# Atualiza o Mayris Pilates na VPS. Rode no servidor, como usuario deploy:
#     bash ~/pilates/deploy/deploy.sh
# Ou de fora, pelo PowerShell do seu computador:  .\deploy.ps1
set -euo pipefail

cd "$(dirname "$0")/.."
RAIZ="$(pwd)"
PY="$RAIZ/.venv/bin/python"

ANTES="$(git rev-parse --short HEAD)"
echo "==> Versao atual no servidor: $ANTES"

# nunca sobrescreve alteracao feita direto no servidor
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "ERRO: ha alteracoes locais no servidor (veja abaixo). Nada foi feito."
  git status --short
  exit 1
fi

git pull --ff-only
DEPOIS="$(git rev-parse --short HEAD)"
if [ "$ANTES" = "$DEPOIS" ]; then
  echo "==> Codigo ja estava atualizado ($DEPOIS)."
else
  echo "==> Atualizado: $ANTES -> $DEPOIS"
  git --no-pager log --oneline "$ANTES..$DEPOIS"
fi

MUDOU="$(git diff --name-only "$ANTES" "$DEPOIS" || true)"

if echo "$MUDOU" | grep -qx 'requirements.txt'; then
  echo "==> requirements.txt mudou: instalando dependencias"
  "$RAIZ/.venv/bin/pip" install -q -r requirements.txt
fi

cd backend
echo "==> Verificando o projeto"
"$PY" manage.py check
echo "==> Migracoes"
"$PY" manage.py migrate --noinput
echo "==> Arquivos estaticos"
"$PY" manage.py collectstatic --noinput | tail -1

echo "==> Reiniciando pilates-web"
sudo systemctl restart pilates-web
if echo "$MUDOU" | grep -Eq '^(api/|shared/|backend/app/)'; then
  echo "==> API (FastAPI) mudou: reiniciando pilates-api"
  sudo systemctl restart pilates-api
fi

sleep 3
echo "==> Situacao dos servicos"
systemctl is-active pilates-web
systemctl is-active pilates-api || true
echo "==> Resposta do site:"
curl -sI https://mayris.mayacorp.com.br/login/ | head -1

echo
echo "Pronto: $DEPOIS no ar."
echo "Para voltar a versao anterior:  git checkout $ANTES -- . && bash deploy/deploy.sh   (ou peca ajuda)"
