FROM debian:bookworm-slim

# frr = roteamento (BGP), snmpd = agente SNMP, stress-ng = demo de sobrecarga
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      frr snmpd snmp jq stress-ng procps iproute2 iputils-ping tcpdump \
 && rm -rf /var/lib/apt/lists/* \
 && sed -i 's/^bgpd=no/bgpd=yes/' /etc/frr/daemons

COPY entrypoint.sh /entrypoint.sh
COPY bgp-rotas.sh /usr/local/bin/bgp-rotas
RUN sed -i 's/\r$//' /entrypoint.sh /usr/local/bin/bgp-rotas \
 && chmod +x /entrypoint.sh /usr/local/bin/bgp-rotas

ENTRYPOINT ["/entrypoint.sh"]
