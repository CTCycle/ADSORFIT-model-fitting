from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, cast
from collections.abc import Callable

from PySide6.QtCore import QFile, QIODevice, QThreadPool, Slot
from PySide6.QtGui import QAction
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
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
        self.configuration = self.config_manager.get_configuration()
        self.dataset_events = DatasetEvents(self.configuration)
        self.fitting_events = FittingEvents(self.configuration)

        self.threadpool = QThreadPool.globalInstance()
        self.worker: ThreadWorker | None = None
        self.progress_bar: QProgressBar | None = None
        self.widgets: dict[str, Any] = {}

        self._setup_configuration(
            [
                # actions
                (QAction, "actionLoadConfig", "load_configuration_action"),
                (QAction, "actionSaveConfig", "save_configuration_action"),
                (QAction, "actionDeleteData", "delete_data_action"),
                (QAction, "actionExportData", "export_data_action"),
                (QAction, "actionReloadApp", "reload_app_action"),
                # progress widgets
                (QPushButton, "stopThread", "stop_thread"),
                (QProgressBar, "progressBar", "progress_bar"),
                # dataset controls
                (QPushButton, "loadDataset", "load_dataset"),
                (QCheckBox, "detectCols", "detect_cols"),
                (QSpinBox, "maxIterations", "max_iterations"),
                # model configuration
                (QPushButton, "runFitting", "run_fitting"),
                (QCheckBox, "selectLangmuir", "select_langmuir"),
                (QDoubleSpinBox, "minLangK", "min_lang_k"),
                (QDoubleSpinBox, "maxLangK", "max_lang_k"),
                (QDoubleSpinBox, "minLangQSat", "min_lang_qsat"),
                (QDoubleSpinBox, "maxLangQSat", "max_lang_qsat"),
            ]
        )

        self.progress_bar = self.widgets.get("progress_bar") if self.widgets else None
        if isinstance(self.progress_bar, QProgressBar):
            self.progress_bar.setValue(0)

        self._set_widgets_from_configuration()

        self._connect_signals(
            [
                ("save_configuration_action", "triggered", self.save_configuration),
                ("load_configuration_action", "triggered", self.load_configuration),
                ("delete_data_action", "triggered", self.delete_database),
                ("export_data_action", "triggered", self.export_database),
                ("reload_app_action", "triggered", self.reload_dataset),
                ("load_dataset", "clicked", self.select_and_load_dataset),
                ("run_fitting", "clicked", self.run_fitting),
                ("stop_thread", "clicked", self.stop_running_worker),
            ]
        )

        self._auto_connect_settings()

    # -------------------------------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        try:
            return self.widgets[name]
        except (AttributeError, KeyError) as e:
            raise AttributeError(
                f"{type(self).__name__!s} has no attribute {name!r}"
            ) from e

    # [SHOW WINDOW]
    ###########################################################################
    def show(self) -> None:
        self.main_win.show()

    # [HELPERS]
    ###########################################################################
    def connect_update_setting(
        self, widget: Any, signal_name: str, config_key: str, getter: Any | None = None
    ) -> None:
        if getter is None:
            if isinstance(widget, (QCheckBox, QRadioButton)):
                getter = widget.isChecked
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                getter = widget.value
            elif isinstance(widget, QComboBox):
                getter = widget.currentText

        signal = getattr(widget, signal_name)
        signal.connect(partial(self._update_single_setting, config_key, getter))

    # -------------------------------------------------------------------------
    def _update_single_setting(self, config_key: str, getter: Any, *args) -> None:
        value = getter()
        self.config_manager.update_value(config_key, value)


    # ---------------------------------------------------------------------
    def connect_update_setting(
        self,
        widget: Any,
        signal_name: str,
        config_key: str,
        getter: Callable[[], Any] | None = None,
    ) -> None:
        if getter is None:
            if isinstance(widget, QCheckBox):
                getter = widget.isChecked
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                getter = widget.value
        signal = getattr(widget, signal_name)
        signal.connect(partial(self._update_single_setting, config_key, getter))

    # ---------------------------------------------------------------------
    def _update_single_setting(self, config_key: str, getter: Callable[[], Any], *args: Any) -> None:
        value = getter()
        self.config_manager.update_value(config_key, value)
        self._refresh_configuration()

    # ---------------------------------------------------------------------
    def _auto_connect_settings(self) -> None:
        bindings = [
            ("detect_cols", "toggled", "detect_cols"),
            ("max_iterations", "valueChanged", "max_iterations"),
            ("select_langmuir", "toggled", "select_langmuir"),
            ("min_lang_k", "valueChanged", "min_lang_k"),
            ("max_lang_k", "valueChanged", "max_lang_k"),
            ("min_lang_qsat", "valueChanged", "min_lang_qsat"),
            ("max_lang_qsat", "valueChanged", "max_lang_qsat"),
        ]

        for attr, signal_name, config_key in connections:
            widget = self.widgets[attr]
            self.connect_update_setting(widget, signal_name, config_key)
            
    # ---------------------------------------------------------------------
    def _setup_configuration(self, widget_defs: list[tuple[type[Any], str, str]]) -> None:
        for cls, name, attr in widget_defs:
            widget = self.main_win.findChild(cls, name)
            if widget is None:
                raise ValueError(f"Widget {name} not found in UI definition")
            setattr(self, attr, widget)
            self.widgets[attr] = widget

    # ---------------------------------------------------------------------
    def _connect_signals(self, connections: list[tuple[str, str, Callable[..., Any]]]) -> None:
        for attr, signal, slot in connections:
            widget = self.widgets[attr]
            getattr(widget, signal).connect(slot)

    # ---------------------------------------------------------------------
    def _set_widgets_from_configuration(self) -> None:
        config = self.config_manager.get_configuration()
        for attr, widget in self.widgets.items():
            if attr not in config:
                continue
            value = config[attr]
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)) and isinstance(
                value, (int, float)
            ):
                widget.setValue(value)

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
        if isinstance(self.progress_bar, QProgressBar):
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
            self.config_manager.save_configuration_to_json(name)
            self._send_message(f"Configuration saved to {name}.json")

    # ---------------------------------------------------------------------
    @Slot()
    def load_configuration(self) -> None:
        dialog = LoadConfigDialog(self.main_win)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selection = dialog.get_selected_config()
            if selection:
                self.config_manager.load_configuration_from_json(selection)
                self._refresh_configuration()
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
        self._refresh_configuration()
        detect_checkbox = self.widgets.get("detect_cols")
        detect = bool(detect_checkbox.isChecked()) if isinstance(detect_checkbox, QCheckBox) else True
        self.worker = ThreadWorker(
            self.dataset_events.load_dataset,
            dataset_path=dataset_path,
            detect_columns=detect,
        )
        target = dataset_path or self.configuration.get("dataset_path")
        self._send_message(f"Loading dataset from {target or 'configured location'}")
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
        self._refresh_configuration()
        if not any(
            self.configuration.get(flag, False)
            for flag in (
                "select_langmuir",
                "select_sips",
                "select_freundlich",
                "select_temkin",
            )
        ):
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
        detect = payload.get("detect_cols")
        columns = payload.get("columns", {})

        if isinstance(path, str):
            self.config_manager.update_value("dataset_path", path)
        if isinstance(detect, bool):
            self.config_manager.update_value("detect_cols", detect)
        for key, config_key in (
            ("experiment", "experiment_column"),
            ("temperature", "temperature_column"),
            ("pressure", "pressure_column"),
            ("uptake", "uptake_column"),
        ):
            value = columns.get(key)
            if value is not None:
                self.config_manager.update_value(config_key, value)

        self._refresh_configuration()
        self._set_widgets_from_configuration()

        stats_text = stats.replace("**", "") if isinstance(stats, str) else "Dataset loaded"
        self._send_message(f"Dataset loaded from {path}")
        QMessageBox.information(self.main_win, "Dataset loaded", stats_text)
        if isinstance(self.progress_bar, QProgressBar):
            self.progress_bar.setValue(0)
        self.worker = None

    # ---------------------------------------------------------------------
    @Slot(object)
    def on_fitting_completed(self, payload: dict[str, Any]) -> None:
        results = payload.get("results")
        if isinstance(results, dict):
            message = f"Fitting completed for {len(results)} experiments"
        else:
            message = "Fitting completed"
        self._send_message(message)
        QMessageBox.information(self.main_win, "Fitting completed", message)
        if isinstance(self.progress_bar, QProgressBar):
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
        if isinstance(self.progress_bar, QProgressBar):
            self.progress_bar.setValue(0)
        self.worker = None

    # ---------------------------------------------------------------------
    def on_task_interrupted(self) -> None:
        self._send_message("Current task interrupted")
        if isinstance(self.progress_bar, QProgressBar):
            self.progress_bar.setValue(0)
        self.worker = None
