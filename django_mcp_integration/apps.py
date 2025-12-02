from django.apps import AppConfig
import logging
import importlib
import inspect
from pathlib import Path

logger = logging.getLogger(__name__)

class DjangoMCPConfig(AppConfig):
    name = "django_mcp_integration"
    verbose_name = "Django MCP Integration"
    
    def ready(self):
        """Enregistre automatiquement les composants MCP depuis toutes les apps"""
        try:
            logger.info("🔍 Début de la détection des outils MCP...")
            self.auto_discover_mcp_tools()
            self.register_tools_to_mcp_server()
            self.register_mcp_components_from_settings()
            
            tools_count = len(self.registry.get_tools())
            logger.info(f"✅ Django MCP Integration initialisée avec {tools_count} outils")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation MCP: {e}")

    @property
    def registry(self):
        from .tools.base import registry
        return registry

    def auto_discover_mcp_tools(self):
        """Découverte automatique des tools MCP dans toutes les apps installées"""
        from django.apps import apps
        
        logger.info("🔍 Scan des applications Django...")
        
        for app_config in apps.get_app_configs():
            logger.debug(f"📦 Scan de l'application: {app_config.name}")
            self._discover_tools_in_app(app_config)

    def _discover_tools_in_app(self, app_config):
        """Découvre les tools MCP dans une app spécifique"""
        app_path = Path(app_config.path)
        logger.debug(f"🔍 Recherche dans: {app_path}")

        # Cherche tools.py (comme models.py)
        tools_file = app_path / "tools.py"
        if tools_file.exists():
            logger.info(f"📄 Fichier tools.py trouvé dans {app_config.name}")
            self._import_and_register_tools(app_config.name, "tools")

        # Cherche mcp_tools.py (alternative)
        mcp_tools_file = app_path / "mcp_tools.py"
        if mcp_tools_file.exists():
            logger.info(f"📄 Fichier mcp_tools.py trouvé dans {app_config.name}")
            self._import_and_register_tools(app_config.name, "mcp_tools")

        # Cherche dans un dossier mcp/
        mcp_dir = app_path / "mcp"
        if mcp_dir.exists() and mcp_dir.is_dir():
            logger.info(f"📁 Dossier mcp/ trouvé dans {app_config.name}")
            self._discover_tools_in_directory(mcp_dir, app_config.name)

    def _import_and_register_tools(self, app_name, module_name):
        """Importe et enregistre les outils d'un module"""
        try:
            full_module_name = f"{app_name}.{module_name}"
            logger.info(f"🔄 Import du module: {full_module_name}")
            
            module = importlib.import_module(full_module_name)
            tools_found = self._register_module_tools(module)
            
            logger.info(f"✅ Module {full_module_name} traité, {tools_found} outils trouvés")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'import de {full_module_name}: {e}")

    def _discover_tools_in_directory(self, directory, app_name):
        """Découvre les tools dans un répertoire"""
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix == ".py" and not file_path.name.startswith("_"):
                module_name = file_path.stem
                full_module_name = f"{app_name}.mcp.{module_name}"
                try:
                    logger.info(f"🔄 Import du module: {full_module_name}")
                    module = importlib.import_module(full_module_name)
                    tools_found = self._register_module_tools(module)
                    logger.info(f"✅ Module {full_module_name} traité, {tools_found} outils trouvés")
                except Exception as e:
                    logger.error(f"❌ Erreur lors de l'import de {full_module_name}: {e}")

    def _register_module_tools(self, module):
        """Enregistre tous les outils MCP d'un module"""
        tools_found = 0
        
        for name, obj in inspect.getmembers(module):
            # Les outils décorés avec @mcp_tool sont déjà dans le registry
            # On les détecte par la présence d'attributs spécifiques
            if (inspect.isclass(obj) and 
                hasattr(obj, '__name__') and
                not name.startswith('_')):
                
                # Vérifie si la classe a une méthode execute (critère principal)
                if hasattr(obj, 'execute') and inspect.iscoroutinefunction(obj.execute):
                    logger.info(f"🎯 Classe outil détectée: {name}")
                    tools_found += 1

        return tools_found

    def register_tools_to_mcp_server(self):
        """Enregistre tous les tools du registry dans le serveur MCP"""
        from .server import mcp_server
        
        tools = self.registry.get_tools()
        logger.info(f"🚀 Enregistrement de {len(tools)} outils dans le serveur MCP...")
        
        for tool_instance in tools:
            try:
                # Récupérer le nom et la description
                tool_name = getattr(tool_instance, 'name', 'unknown_tool')
                tool_description = getattr(tool_instance, 'description', 'No description')
                # input_schema = getattr(tool_instance, 'input_schema', {})
                
                # Créer un wrapper pour l'outil avec signature explicite
                async def tool_wrapper(parm):
                    return await tool_instance.execute(parm)
                
                # Définir le nom de la fonction
                tool_wrapper.__name__ = tool_name
                
                # Enregistrer dans le serveur MCP avec le schéma
                mcp_server.tool(
                    name=tool_name,
                    description=tool_description,
                    # input_schema=input_schema
                )(tool_wrapper)
                
                logger.info(f"✅ Outil MCP enregistré: {tool_name}")
                
            except Exception as e:
                logger.error(f"❌ Erreur avec l'outil {getattr(tool_instance, 'name', 'unknown')}: {e}")
    
    def register_mcp_components_from_settings(self):
        """Enregistre les composants depuis les settings (rétrocompatibilité)"""
        from django.conf import settings
        
        # Enregistrement des outils depuis les settings
        for tool_path in getattr(settings, "MCP_TOOLS", []):
            self._register_component_from_settings(tool_path, "tool")

    def _register_component_from_settings(self, component_path, component_type):
        """Enregistre un composant depuis les settings"""
        try:
            module_path, component_name = component_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            component = getattr(module, component_name)
            
            if component_type == "tool":
                # Enregistrer directement dans le serveur MCP
                from .server import mcp_server
                mcp_server.tool()(component)
                logger.info(f"✅ Outil enregistré depuis settings: {component_path}")
                    
        except (ImportError, AttributeError, ValueError) as e:
            logger.error(f"❌ Erreur avec {component_path}: {e}")