"""Diagramas UML de componentes y de despliegue (Graphviz). Uso: python3 gen_arquitectura.py <destino>

QUÉ HACE: escribe en <destino>/arquitectura los diagramas CO01 (componentes), CO02 (capas de una app de Django)
y DE01 (despliegue: servidor, finca, pasarela IoT, celulares), cada uno como .dot, .svg y .png.
CÓMO: el texto de cada diagrama está escrito aquí en lenguaje DOT; el programa dot de Graphviz lo dibuja.
REQUISITO: Graphviz instalado (comando dot).
"""
import os
import subprocess
import sys

DEST = os.path.join(sys.argv[1], 'arquitectura')
os.makedirs(DEST, exist_ok=True)
CAB = ('graph [fontname="DejaVu Sans", pad=0.3, bgcolor=white, labelloc=t, fontsize=16, nodesep=0.35, ranksep=0.7, compound=true];'
       'node [fontname="DejaVu Sans", fontsize=11, shape=box, style="rounded,filled", fillcolor="#FFFFFF", color="#4B5563"];'
       'edge [fontname="DejaVu Sans", fontsize=9.5, color="#6B7280", fontcolor="#4B5563", arrowhead=vee];')

COMPONENTES = 'digraph C {' + CAB + '''
label="Componentes de GuayacanERP: el ERP es el único que escribe en PostgreSQL";
rankdir=LR;
subgraph cluster_cli { label="Clientes"; style="rounded,dashed"; color="#9CA3AF";
  pwa [label="«componente»\\nPWA de campo (Angular)\\nservice worker + IndexedDB"];
  panel [label="«componente»\\nPanel administrativo (Angular)"];
  portal [label="«componente»\\nPortal y tienda de clientes"];
}
subgraph cluster_ext { label="Externos"; style="rounded,dashed"; color="#9CA3AF";
  canales [label="«sistema»\\nWhatsApp, Instagram,\\nMessenger, TikTok"];
  dian [label="«sistema»\\nDIAN (factura, soporte, nómina)"];
  pagos [label="«sistema»\\nPasarela de pagos"];
  llm [label="«sistema»\\nProveedor de IA (Claude)"];
  b2b [label="«sistema»\\nCliente B2B (fase 3)"];
}
gw [label="«componente»\\nPasarela IoT local\\nMosquitto + reglas", fillcolor="#FFF7ED"];
nginx [label="«componente»\\nNginx\\nHTTPS, límites, rutas"];
subgraph cluster_erp { label="Núcleo ERP · Django + DRF (monolito modular, 25 apps)"; style=rounded; color="#2E6B4F"; fontcolor="#2E6B4F";
  api [label="«componente»\\nAPI REST /api/v1\\nOpenAPI (drf-spectacular)", fillcolor="#EAF3EE"];
  mw [label="«componente»\\nContextoFinca\\nJWT + set_config", fillcolor="#EAF3EE"];
  serv [label="«componente»\\nServicios (casos de uso)\\npor app", fillcolor="#EAF3EE"];
  celery [label="«componente»\\nCelery + Beat\\ntareas, outbox, facturación", fillcolor="#EAF3EE"];
  mcp [label="«componente»\\nServidor MCP\\nherramientas de agentes", fillcolor="#EAF3EE"];
}
subgraph cluster_ag { label="Servicio de agentes · FastAPI"; style=rounded; color="#7A4E9C"; fontcolor="#7A4E9C";
  webhooks [label="«componente»\\nWebhooks de canales"];
  orq [label="«componente»\\nOrquestador + 14 agentes\\n(LangGraph, LiteLLM)"];
}
subgraph cluster_datos { label="Datos"; style=rounded; color="#4B5563";
  pg [label="«base de datos»\\nPostgreSQL 18\\n246 tablas, RLS, reglas", shape=cylinder, fillcolor="#EEF2FF"];
  mongo [label="«base de datos»\\nMongoDB\\nconversaciones, bitácoras", shape=cylinder, fillcolor="#EEF2FF"];
  redis [label="«base de datos»\\nRedis\\ncolas, caché, streams", shape=cylinder, fillcolor="#EEF2FF"];
  minio [label="«almacén»\\nMinIO (S3)\\nfotos, PDF, XML", shape=folder, fillcolor="#EEF2FF"];
}
pwa -> nginx [label="HTTPS + JWT"]; panel -> nginx; portal -> nginx; b2b -> nginx [label="llave API"];
nginx -> mw; mw -> api; api -> serv; serv -> pg [label="SQL como guayacan_app"]; serv -> minio;
celery -> pg [label="outbox"]; celery -> redis [label="Redis Streams"]; celery -> dian; pagos -> api [label="webhook"];
canales -> webhooks [label="webhook firmado"]; webhooks -> orq; orq -> llm; orq -> mongo; orq -> redis [label="eventos"];
orq -> mcp [label="herramientas"]; mcp -> api [label="token del agente"];
gw -> api [label="lecturas y comandos (MQTT puente)"];
}'''

DESPLIEGUE = 'digraph D {' + CAB + '''
label="Despliegue: fase 1 en un VPS con Docker Compose; la finca no depende de un servidor propio";
rankdir=TB;
node [shape=box3d, style=filled, fillcolor="#F9FAFB"];
subgraph cluster_finca { label="«nodo» Finca El Guayacán (Pueblo Nuevo, Nilo)"; style=rounded; color="#2E6B4F"; fontcolor="#2E6B4F";
  cel [label="«dispositivo»\\nCelulares y tabletas\\nPWA instalada"];
  lect [label="«dispositivo»\\nLectores de código y básculas\\nBluetooth / USB"];
  pas [label="«dispositivo»\\nPasarela local (Raspberry Pi o mini PC)\\nMosquitto, reglas, NVR de cámaras"];
  esp [label="«dispositivo»\\nNodos ESP32 / PLC\\nsensores y actuadores (fase 4)"];
}
subgraph cluster_nube { label="«nodo» Nube · VPS (fase 1) → Kubernetes (cuando crezca)"; style=rounded; color="#4B5563";
  subgraph cluster_compose { label="«entorno de ejecución» Docker Compose"; style="rounded,dashed"; color="#9CA3AF";
    n1 [label="«contenedor» nginx", shape=component, fillcolor="#FFFFFF"];
    n2 [label="«contenedor» erp (gunicorn + Django)", shape=component, fillcolor="#EAF3EE"];
    n3 [label="«contenedor» celery-worker + celery-beat", shape=component, fillcolor="#EAF3EE"];
    n4 [label="«contenedor» agentes (uvicorn + FastAPI)", shape=component, fillcolor="#F5F0FA"];
    n5 [label="«contenedor» postgres 18 + PostGIS + pgvector", shape=component, fillcolor="#EEF2FF"];
    n6 [label="«contenedor» mongodb 8", shape=component, fillcolor="#EEF2FF"];
    n7 [label="«contenedor» redis 7", shape=component, fillcolor="#EEF2FF"];
    n8 [label="«contenedor» minio", shape=component, fillcolor="#EEF2FF"];
  }
  bk [label="«almacén externo»\\nCopias cifradas 3-2-1\\nprueba de restauración mensual"];
}
subgraph cluster_saas { label="«nodo» Servicios externos"; style="rounded,dashed"; color="#9CA3AF";
  e1 [label="DIAN"]; e2 [label="Meta y TikTok"]; e3 [label="Proveedor de IA"]; e4 [label="Pasarela de pagos"];
}
cel -> n1 [label="HTTPS 443 (4G o wifi)"]; lect -> cel [label="Bluetooth / HID", arrowhead=none];
esp -> pas [label="MQTT en red local", arrowhead=none]; pas -> n1 [label="HTTPS / MQTT sobre TLS cuando hay internet"];
n1 -> n2; n1 -> n4; n2 -> n5; n3 -> n5; n3 -> n7; n4 -> n6; n4 -> n7; n2 -> n8; n5 -> bk [label="pgBackRest / pg_dump cifrado"];
n3 -> e1; n4 -> e2; n4 -> e3; e4 -> n1 [label="webhook"];
}'''

CAPAS = 'digraph K {' + CAB + '''
label="Cuatro capas dentro de cada app de Django: cada capa solo llama a la de abajo";
rankdir=TB; node [width=6.5, fixedsize=false];
a [label="API · views.py y serializers.py\\nvalida formato, permisos de DRF, pagina, documenta OpenAPI", fillcolor="#EAF3EE"];
s [label="Servicios · services.py\\nun método por caso de uso, abre la transacción, coordina, publica el evento", fillcolor="#EAF3EE"];
d [label="Dominio · reglas en PostgreSQL (reglas_negocio.sql)\\nlas reglas críticas viven en la base; Python no las duplica", fillcolor="#FFF7ED"];
r [label="Adaptadores · models.py (managed=False), clientes de DIAN, MinIO, canales, IA\\nPatrón puerto y adaptador: se cambian sin tocar los servicios", fillcolor="#EEF2FF"];
a -> s -> d -> r;
}'''

for nombre, codigo in (('CO01_componentes', COMPONENTES), ('DE01_despliegue', DESPLIEGUE), ('CO02_capas_app', CAPAS)):
    base = os.path.join(DEST, nombre)
    open(base + '.dot', 'w', encoding='utf-8').write(codigo)
    subprocess.run(['dot', '-Tsvg', base + '.dot', '-o', base + '.svg'], check=True)
    subprocess.run(['dot', '-Gdpi=130', '-Tpng', base + '.dot', '-o', base + '.png'], check=True)
    print(base)
