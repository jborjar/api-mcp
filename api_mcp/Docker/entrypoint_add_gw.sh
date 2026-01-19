#!/bin/bash

ip route add 10.0.0.0/8 via 172.19.50.254 || echo "No se pudo agregar la ruta LAN"
ip route add 172.16.1.0/24 via 172.19.50.254 || echo "No se pudo agregar la ruta LAN"

exec "$@"
