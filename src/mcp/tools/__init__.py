import importlib
import logging
import os

logger = logging.getLogger(__name__)

tools_dir = os.path.dirname(__file__)

for filename in os.listdir(tools_dir):
    if filename.endswith(".py") and filename != "__init__.py":
        module_name = filename[:-3]

        try:
            importlib.import_module(f".{module_name}", package=__name__)
            logger.info(f"Auto-registered tools from: {module_name}")
        except Exception as e:
            logger.error(f"Failed to import tool module {module_name}: {e}")

logger.info("All Weather MCP tools have been auto-registered")
