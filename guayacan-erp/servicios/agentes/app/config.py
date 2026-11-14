"""Ajustes del servicio de agentes, leídos de las variables de entorno (.env). Ningún secreto va en el código.

@dataclass(frozen=True) crea una clase de solo lectura: una vez cargados, los ajustes no se pueden cambiar
por error en otra parte del programa. field(default_factory=...) lee la variable en el momento de crear el objeto.
"""
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Ajustes:
    # Dirección del ERP (Django)
    erp_url: str = field(default_factory=lambda: os.environ.get('ERP_URL', 'http://localhost:8000'))
    # Dirección de las herramientas MCP del ERP que usan los agentes
    mcp_url: str = field(default_factory=lambda: os.environ.get('MCP_URL', 'http://localhost:8000/mcp/'))
    # MongoDB: conversaciones y mensajes
    mongo_url: str = field(default_factory=lambda: os.environ.get('MONGO_URL', 'mongodb://localhost:27017/guayacan'))
    # Redis: cola de mensajes entrantes y eventos del ERP
    redis_url: str = field(default_factory=lambda: os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    # Token que se escribe en la consola de Meta al registrar el webhook
    meta_token_verificacion: str = field(default_factory=lambda: os.environ.get('META_TOKEN_VERIFICACION', ''))
    # Secreto de la app de Meta: sirve para verificar la firma de cada mensaje
    meta_secreto_app: str = field(default_factory=lambda: os.environ.get('META_SECRETO_APP', ''))
    # Modelo de IA por defecto (LiteLLM permite cambiar de proveedor sin cambiar código)
    modelo_ia: str = field(default_factory=lambda: os.environ.get('MODELO_IA', 'claude-sonnet-5-5'))


# Instancia única que importan los demás módulos:  from .config import ajustes
ajustes = Ajustes()
