import importlib
import logging
import os

logger = logging.getLogger(__name__)

# Get the absolute path to this directory
tools_dir = os.path.dirname(__file__)

# Track successfully registered modules
registered_modules = []

# Loop through all Python files in this directory
for filename in os.listdir(tools_dir):
    # Only consider .py files excluding __init__.py and hidden files
    if (
        filename.endswith(".py")
        and not filename.startswith("_")
        and filename != "__init__.py"
    ):
        module_name = filename[:-3]  # remove ".py"

        try:
            # Perform a relative import using importlib
            importlib.import_module(f".{module_name}", package=__name__)
            logger.info(f"Registered tool module: {module_name}")
            registered_modules.append(module_name)

        except Exception as e:
            logger.error(
                f"Failed to import tool module '{module_name}': {type(e).__name__}: {e}"
            )

# Summary log after all modules are processed
if registered_modules:
    logger.info(
        f"Auto-registration complete. Loaded tools: {', '.join(registered_modules)}"
    )
else:
    logger.warning("No tool modules were successfully registered.")
