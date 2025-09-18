from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QListWidget,
    QVBoxLayout,
    QLabel,
)

from ADSORFIT.app.constants import CONFIG_PATH


###############################################################################
class SaveConfigDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Save Configuration")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter a name for your configuration:", self))

        self.name_edit = QLineEdit(self)
        layout.addWidget(self.name_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        layout.addWidget(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    # -------------------------------------------------------------------------
    def get_name(self) -> str:
        return self.name_edit.text().strip()


###############################################################################
class LoadConfigDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Load Configuration")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select a configuration:", self))

        self.config_list = QListWidget(self)
        layout.addWidget(self.config_list)

        config_dir = Path(CONFIG_PATH)
        config_dir.mkdir(parents=True, exist_ok=True)
        for path in sorted(config_dir.glob("*.json")):
            self.config_list.addItem(path.name)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        layout.addWidget(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    # -------------------------------------------------------------------------
    def get_selected_config(self) -> str | None:
        item = self.config_list.currentItem()
        return item.text() if item else None
