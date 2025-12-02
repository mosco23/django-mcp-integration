from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django_mcp_integration.server import mcp_server, MCP_CONFIG
from django.conf import settings
import asyncio

class Command(BaseCommand):
    help = "Lance le serveur MCP intégré à Django"
    
    def add_arguments(self, parser):
        parser.add_argument(
            "--host",
            default=getattr(settings, "MCP_HOST", MCP_CONFIG["host"]),
            help="Host du serveur MCP",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=getattr(settings, "MCP_PORT", MCP_CONFIG["port"]),
            help="Port du serveur MCP",
        )
        # parser.add_argument(
        #     "--transport",
        #     choices=["stdio", "http", "sse", "streamable-http"],
        #     default=getattr(settings, "MCP_TRANSPORT", MCP_CONFIG["transport"]),
        #     help="Transport MCP à utiliser",
        # )
        parser.add_argument(
            "--no-banner",
            action="store_true",
            help="Désactive l'affichage de la bannière",
        )

    def handle(self, *args, **options):
        host = options["host"]
        port = options["port"]
        # transport = options["transport"]
        show_banner = not options["no_banner"]

        self.stdout.write(
            self.style.SUCCESS(
                f"Démarrage du serveur MCP Django sur {host}:{port} avec le transport {MCP_CONFIG["transport"]}"
            )
        )

        # Lance le serveur MCP
        try:
            asyncio.run(
                mcp_server.run_http_async(
                    transport=MCP_CONFIG["transport"],
                    host=host,
                    port=port,
                    show_banner=show_banner
                )
            )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Arrêt du serveur MCP..."))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Erreur du serveur MCP: {e}")
            )
            raise CommandError(f"Erreur du serveur MCP: {e}")