from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, cast

from PySide6.QtCore import QFile, QIODevice, QThreadPool, Slot
from PySide6.QtGui import QAction
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
)
from qt_material import apply_stylesheet

from ADSORFIT.app.client.dialogs import LoadConfigDialog, SaveConfigDialog
from ADSORFIT.app.client.events import DatasetEvents, FittingEvents
from ADSORFIT.app.client.workers import ThreadWorker
from ADSORFIT.app.configuration import Configuration
from ADSORFIT.app.logger import logger


###############################################################################
def apply_style(app: QApplication) -> QApplication:
    theme = "dark_yellow"
    extra = {"density_scale": "-1"}
    apply_stylesheet(app, theme=f"{theme}.xml", extra=extra)
    app.setStyleSheet(
        app.styleSheet()
        + """
    QProgressBar {
        text-align: center;
        color: black;
        font-weight: bold;
    }
    """
    )
    return app


###############################################################################
class MainWindow:
    def __init__(self, ui_file_path: str) -> None:
        loader = QUiLoader()
        ui_file = QFile(ui_file_path)
        ui_file.open(QIODevice.OpenModeFlag.ReadOnly)
        self.main_win = cast(QMainWindow, loader.load(ui_file))
        ui_file.close()
        self.main_win.showMaximized()

        self.config_manager = Configuration()
        self.dataset_events = DatasetEvents(self.config_manager)
        self.fitting_events = FittingEvents(self.config_manager)

        self.threadpool = QThreadPool.globalInstance()
        self.worker: ThreadWorker | None = None

        self.widgets: dict[str, Any] = {}
        self.actions: dict[str, QAction] = {}
        self._register_widgets()
        self._register_actions()
        self._set_widgets_from_configuration()
        self._connect_actions()
        self._connect_buttons()
        self._auto_connect_settings()
        self._set_states()

    # ---------------------------------------------------------------------
    def show(self) -> None:
        self.main_win.show()

    # ---------------------------------------------------------------------
    def _register_widgets(self) -> None:
        definitions = [
            (QCheckBox, "detectCols", "detectCols"),
            (QSpinBox, "maxIterations", "maxIterations"),
            (QPushButton, "loadDataset", "loadDataset"),
            (QPushButton, "runFitting", "runFitting"),
            (QCheckBox, "selectLangmuir", "selectLangmuir"),
            (QDoubleSpinBox, "minLangK", "minLangK"),
            (QDoubleSpinBox, "maxLangK", "maxLangK"),
            (QDoubleSpinBox, "minLangQSat", "minLangQSat"),
            (QDoubleSpinBox, "maxLangQSat", "maxLangQSat"),
            (QProgressBar, "progressBar", "progressBar"),
            (QPushButton, "stopThread", "stopThread"),
        ]
        for cls, name, key in definitions:
            widget = self.main_win.findChild(cls, name)
            if widget is None:
                raise ValueError(f"Widget {name} not found in UI definition")
            self.widgets[key] = widget

    # ---------------------------------------------------------------------
    def _register_actions(self) -> None:
        mapping = [
            ("actionSaveConfig", "saveConfig"),
            ("actionLoadConfig", "loadConfig"),
            ("actionDeleteData", "deleteData"),
            ("actionExportData", "exportData"),
            ("actionReloadApp", "reloadApp"),
        ]
        for name, key in mapping:
            action = self.main_win.findChild(QAction, name)
            if action is None:
                raise ValueError(f"Action {name} not found in UI definition")
            self.actions[key] = action

    # ---------------------------------------------------------------------
    def _connect_actions(self) -> None:
        self.actions["saveConfig"].triggered.connect(self.save_configuration)
        self.actions["loadConfig"].triggered.connect(self.load_configuration)
        self.actions["deleteData"].triggered.connect(self.delete_database)
        self.actions["exportData"].triggered.connect(self.export_database)
        self.actions["reloadApp"].triggered.connect(self.reload_dataset)

    # ---------------------------------------------------------------------
    def _connect_buttons(self) -> None:
        self.widgets["loadDataset"].clicked.connect(self.select_and_load_dataset)
        self.widgets["runFitting"].clicked.connect(self.run_fitting)
        self.widgets["stopThread"].clicked.connect(self.stop_running_worker)

    # ---------------------------------------------------------------------
    def _auto_connect_settings(self) -> None:
        bindings = [
            ("detectCols", "toggled"),
            ("maxIterations", "valueChanged"),
            ("selectLangmuir", "toggled"),
            ("minLangK", "valueChanged"),
            ("maxLangK", "valueChanged"),
            ("minLangQSat", "valueChanged"),
            ("maxLangQSat", "valueChanged"),
        ]
        for key, signal_name in bindings:
            widget = self.widgets[key]
            signal = getattr(widget, signal_name)
            signal.connect(partial(self._update_setting, key))

    # ---------------------------------------------------------------------
    def _update_setting(self, key: str, value: Any) -> None:
        self.config_manager.update_value(key, value)

    # ---------------------------------------------------------------------
    def _set_widgets_from_configuration(self) -> None:
        config = self.config_manager.get_configuration()
        for key, widget in self.widgets.items():
            if key not in config:
                continue
            value = config[key]
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)) and isinstance(
                value, (int, float)
            ):
                widget.setValue(value)

    # ---------------------------------------------------------------------
    def _set_states(self) -> None:
        self.progress_bar: QProgressBar = self.widgets["progressBar"]
        self.progress_bar.setValue(0)

    # ---------------------------------------------------------------------
    def _send_message(self, message: str) -> None:
        self.main_win.statusBar().showMessage(message, 5000)

    # ---------------------------------------------------------------------
    def _start_thread_worker(
        self,
        worker: ThreadWorker,
        on_finished,
        on_error,
        on_interrupted,
    ) -> None:
        self.progress_bar.setValue(0)
        worker.signals.progress.connect(self.progress_bar.setValue)
        worker.signals.finished.connect(on_finished)
        worker.signals.error.connect(on_error)
        worker.signals.interrupted.connect(on_interrupted)
        self.threadpool.start(worker)

    ###########################################################################
    # Slots
    ###########################################################################
    @Slot()
    def stop_running_worker(self) -> None:
        if self.worker is not None:
            self.worker.stop()
            self._send_message("Stopping current task...")

    # ---------------------------------------------------------------------
    @Slot()
    def save_configuration(self) -> None:
        dialog = SaveConfigDialog(self.main_win)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_name() or "default"
            path = self.config_manager.save_configuration_to_json(name)
            self._send_message(f"Configuration saved to {path.name}")

    # ---------------------------------------------------------------------
    @Slot()
    def load_configuration(self) -> None:
        dialog = LoadConfigDialog(self.main_win)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selection = dialog.get_selected_config()
            if selection:
                self.config_manager.load_configuration_from_json(selection)
                self._set_widgets_from_configuration()
                self._send_message(f"Configuration {selection} loaded")

    # ---------------------------------------------------------------------
    @Slot()
    def select_and_load_dataset(self) -> None:
        if self.worker is not None:
            QMessageBox.warning(
                self.main_win,
                "Application busy",
                "A task is already running. Please wait for it to finish.",
            )
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_win,
            "Select adsorption dataset",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return
        self._queue_dataset_load(file_path)

    # ---------------------------------------------------------------------
    @Slot()
    def reload_dataset(self) -> None:
        if self.worker is not None:
            QMessageBox.warning(
                self.main_win,
                "Application busy",
                "A task is already running. Please wait for it to finish.",
            )
            return
        self._queue_dataset_load(None)

    # ---------------------------------------------------------------------
    def _queue_dataset_load(self, dataset_path: str | None) -> None:
        detect = self.widgets["detectCols"].isChecked()
        self.worker = ThreadWorker(
            self.dataset_events.load_dataset,
            dataset_path=dataset_path,
            detect_columns=detect,
        )
        target = dataset_path or self.config_manager.get_configuration().get("datasetPath")
        self._send_message(
            f"Loading dataset from {target or 'configured location'}"
        )
        self._start_thread_worker(
            self.worker,
            on_finished=self.on_dataset_loaded,
            on_error=self.on_error,
            on_interrupted=self.on_task_interrupted,
        )

    # ---------------------------------------------------------------------
    @Slot()
    def run_fitting(self) -> None:
        if self.worker is not None:
            QMessageBox.warning(
                self.main_win,
                "Application busy",
                "A task is already running. Please wait for it to finish.",
            )
            return
        if not self.config_manager.get_model_configuration():
            QMessageBox.warning(
                self.main_win,
                "No models selected",
                "Enable at least one adsorption model before running the fitting pipeline.",
            )
            return
        self.worker = ThreadWorker(self.fitting_events.run_fitting)
        self._send_message("Running adsorption model fitting...")
        self._start_thread_worker(
            self.worker,
            on_finished=self.on_fitting_completed,
            on_error=self.on_error,
            on_interrupted=self.on_task_interrupted,
        )

    # ---------------------------------------------------------------------
    @Slot()
    def delete_database(self) -> None:
        reply = QMessageBox.question(
            self.main_win,
            "Delete data",
            "This will remove all stored datasets and results. Continue?",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.dataset_events.clear_database()
            self._send_message("Database cleared")

    # ---------------------------------------------------------------------
    @Slot()
    def export_database(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self.main_win,
            "Select export directory",
        )
        if not directory:
            return
        target = self.dataset_events.export_database(Path(directory))
        self._send_message(f"Database exported to {target}")

    ###########################################################################
    # Worker callbacks
    ###########################################################################
    @Slot(object)
    def on_dataset_loaded(self, payload: dict[str, Any]) -> None:
        path = payload.get("path")
        stats = payload.get("stats", "Dataset loaded successfully.")
        stats_text = stats.replace("**", "")
        self._send_message(f"Dataset loaded from {path}")
        QMessageBox.information(self.main_win, "Dataset loaded", stats_text)
        self.progress_bar.setValue(0)
        self.worker = None

    # ---------------------------------------------------------------------
    @Slot(object)
    def on_fitting_completed(self, payload: dict[str, Any]) -> None:
        results = payload.get("results")
        if results is not None:
            message = f"Fitting completed for {len(results)} experiments"
        else:
            message = "Fitting completed"
        self._send_message(message)
        QMessageBox.information(self.main_win, "Fitting completed", message)
        self.progress_bar.setValue(0)
        self.worker = None

    # ---------------------------------------------------------------------
    def on_error(self, err_tb: tuple[Exception, str]) -> None:
        exc, tb = err_tb
        logger.error("%s\n%s", exc, tb)
        QMessageBox.critical(
            self.main_win,
            "Operation failed",
            "An error occurred during the operation. Check logs for details.",
        )
        self.progress_bar.setValue(0)
        self.worker = None

    # ---------------------------------------------------------------------
    def on_task_interrupted(self) -> None:
        self._send_message("Current task interrupted")
        self.progress_bar.setValue(0)
        self.worker = None
