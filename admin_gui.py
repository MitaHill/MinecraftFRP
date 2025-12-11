import sys
import json
import os
from PySide6.QtWidgets import QApplication, QInputDialog, QLineEdit, QMessageBox
from src_admin_gui.AdminMainWindow import AdminMainWindow
from src_admin_gui.AdminClient import AdminClient
from src_admin_gui.LogManager import get_logger

logger = get_logger()

CONFIG_FILE = "admin_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
    return {}

def save_config(key):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"admin_key": key}, f)
    except Exception as e:
        logger.error(f"Failed to save config: {e}")

def main():
    """Admin GUI application entry point."""
    app = QApplication(sys.argv)
    
    config = load_config()
    saved_key = config.get("admin_key")
    
    key = saved_key
    
    # Simple check if key is valid (optional, or just ask if not saved)
    if not key:
        # Ask for Admin Key
        key, ok = QInputDialog.getText(None, "Admin Login", "Enter Admin Key:", echo=QLineEdit.Password)
        if not ok or not key:
            return
            
        # Ask to save
        if QMessageBox.question(None, "Save Key", "Save Admin Key for future use?") == QMessageBox.Yes:
            save_config(key)
            
    AdminClient.set_key(key)
    
    window = AdminMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
