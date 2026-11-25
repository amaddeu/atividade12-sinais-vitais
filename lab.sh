#!/bin/bash
# Atividade 12 - "Sinais Vitais": atalhos do lab (Linux, macOS, WSL ou GitHub Codespaces).
# Só precisa de Docker com o plugin "docker compose". Uso: ./lab.sh <comando>
set -e
cd "$(dirname "$0")"

uso() {
cat <<'TXT'
Uso: ./lab.sh <comando>

  iniciar      sobe os 6 containers e configura o Zabbix sozinho (1a vez: 3 a 6 min)
  status       valores atuais, problemas ativos e e-mails enviados (via API do Zabbix)
  painel       status atualizado a cada 15 s (Ctrl+C sai)
  testes       sessao BGP + 4 testes de seguranca do SNMPv3
  demo [min]   ISP manda +10.000 rotas e a CPU do roteador vai a 100% (padrao 8 min)
  parar-demo   para o estresse e retira as rotas extras
  email        configura o envio REAL de e-mail (Gmail + senha de app) - opcional
  desligar     para os containers (configuracao e historico preservados)
  apagar       remove tudo, inclusive o banco do Zabbix (volta do zero)
TXT
}

compose() { docker compose "$@"; }
prefixos() { docker exec roteador-borda bgp-rotas 2>/dev/null || echo 0; }
status_py() { compose run --rm --no-deps configurador python scripts/status.py; }

esperar_docker() {
  for i in $(seq 1 60); do docker info >/dev/null 2>&1 && return 0; sleep 2; done
  echo "ERRO: o Docker nao esta rodando. Abra o Docker (Docker Desktop no Windows/macOS) e tente de novo."; exit 1
}

case "${1:-}" in
  iniciar)
    esperar_docker
    echo ">> 1/3 Subindo os containers (a 1a vez baixa ~600 MB e constroi a imagem do roteador)"
    compose up -d --build
    echo; echo ">> 2/3 Configurando o Zabbix pela API (host, itens, triggers, NOC, action)"
    docker logs -f zbx-configurador || true
    if [ "$(docker wait zbx-configurador)" != "0" ]; then
      echo "ERRO: a configuracao do Zabbix falhou (veja acima). Rode ./lab.sh iniciar de novo."; exit 1
    fi
    echo; echo ">> 3/3 Conferindo o BGP"
    for i in $(seq 1 45); do P=$(prefixos); [ "${P:-0}" -gt 0 ] 2>/dev/null && break; sleep 2; done
    echo "   Prefixos BGP recebidos do ISP: $P"
    echo
    echo "============  LAB PRONTO: http://localhost:8080   (Admin / zabbix)  ============"
    [ -n "$CODESPACES" ] && echo "   (Codespaces: abra a aba PORTS e clique no globo da porta 8080)"
    echo "   Proximos passos: ./lab.sh testes  |  ./lab.sh demo  |  ./lab.sh painel"
    ;;
  status) status_py ;;
  painel)
    while true; do
      clear
      echo "=========  LAB ATIVIDADE 12 - SINAIS VITAIS  |  $(date +%H:%M:%S)  |  Ctrl+C para sair  ========="
      status_py 2>&1 || echo "(Zabbix ainda subindo...)"
      sleep 15
    done ;;
  testes) docker exec roteador-borda bash /scripts/testes.sh ;;
  demo)
    MIN="${2:-8}"
    echo ">> ISP anunciando +10.000 rotas para o roteador de borda..."
    docker exec isp-transito bash /scripts/rotas.sh anunciar
    sleep 5; echo "   Prefixos recebidos agora: $(prefixos)"
    echo ">> Estressando TODOS os nucleos do roteador a 100% por $MIN minutos (stress-ng)..."
    docker exec -d roteador-borda stress-ng --cpu 0 --cpu-load 100 --timeout "${MIN}m"
    echo "   Inicio: $(date +%H:%M:%S). A media de 5 min passa de 90% em ~6 min -> trigger DISASTER -> e-mail ao NOC."
    echo "   Acompanhe: ./lab.sh painel  ou  http://localhost:8080 > Monitoring > Problems"
    ;;
  parar-demo)
    docker exec roteador-borda pkill stress-ng 2>/dev/null && echo ">> stress-ng parado" || echo ">> stress-ng nao estava rodando"
    docker exec isp-transito bash /scripts/rotas.sh retirar
    sleep 3; echo ">> Rotas extras retiradas. Prefixos agora: $(prefixos)"
    ;;
  email)
    read -rp "Gmail que ENVIA o alerta (remetente): " G
    read -rp "E-mail do NOC que RECEBE o alerta: " N
    compose run --rm --no-deps configurador python scripts/configurar_email.py --gmail "$G" --noc "$N"
    echo "Senha de app do Gmail (16 letras, criada em https://myaccount.google.com/apppasswords):"
    compose run --rm --no-deps -it configurador python scripts/configurar_senha.py
    ;;
  desligar) compose stop ;;
  apagar) compose down -v ;;
  *) uso ;;
esac
