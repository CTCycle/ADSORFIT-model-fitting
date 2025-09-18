from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from ADSORFIT.app.variables import EnvironmentVariables

EV = EnvironmentVariables()

from functools import partial

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
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTextEdit,
)
from qt_material import apply_stylesheet

from ADSORFIT.app.client.dialogs import LoadConfigDialog, SaveConfigDialog
from ADSORFIT.app.client.events import (
    BenchmarkEvents,
    DatasetEvents,
    VisualizationEnvents,
)
from ADSORFIT.app.client.workers import ThreadWorker
from ADSORFIT.app.configuration import Configuration
from ADSORFIT.app.logger import logger
from ADSORFIT.app.utils.data.database import database


###############################################################################
def apply_style(app: QApplication) -> QApplication:
    theme = "dark_yellow"
    extra = {"density_scale": "-1"}
    apply_stylesheet(app, theme=f"{theme}.xml", extra=extra)

    # Make % text visible/centered for ALL progress bars
    app.setStyleSheet(
        app.styleSheet()
        + """
    QProgressBar {
        text-align: center;   /* align percentage to the center */
        color: black;        /* black text for yellow bar */
        font-weight: bold;   /* bold percentage */        
    }
    """
    )

    return app


###############################################################################
class MainWindow:
    
    def __init__(self, ui_file_path: str) -> None: 
        super().__init__()
        loader = QUiLoader()
        ui_file = QFile(ui_file_path)
        ui_file.open(QIODevice.OpenModeFlag.ReadOnly)
        self.main_win = cast(QMainWindow, loader.load(ui_file))
        ui_file.close()
        self.main_win.showMaximized()

        self.tokenizers = []

        # initial settings
        self.config_manager = Configuration()
        self.configuration = self.config_manager.get_configuration()

        # set thread pool for the workers
        self.threadpool = QThreadPool.globalInstance()
        self.worker: ThreadWorker | None = None        

        # initialize database
        database.initialize_database()

        # persistent handlers
        self.loading_handler = DatasetEvents(self.configuration, self.hf_access_token)        
        self.benchmark_handler = BenchmarkEvents(self.configuration, self.hf_access_token)
        self.viewer_handler = VisualizationEnvents(self.configuration)

        # setup UI elements
        self._set_states()
        self.widgets = {}
        self._setup_configuration([
            # actions
            (QAction, 'actionLoadConfig', 'load_configuration_action'),
            (QAction, 'actionSaveConfig', 'save_configuration_action'),
            # progress widgets
            (QPushButton,'stopThread','stop_thread'),
            (QProgressBar, "progressBar", 'progress_bar'),
            # dataset selection and analysis
            (QPushButton, "loadDataset", 'load_dataset'),
            (QPushButton, "analyzeDataset", 'analyze_dataset'), 
            (QCheckBox, "useCustomDataset", 'use_custom_dataset'),
            (QCheckBox, "removeInvalid", 'remove_invalid_docs'),
            (QCheckBox, "includeCustomToken", 'custom_tokenizer'),
            (QSpinBox,  "numDocs", 'num_documents'),
            (QTextEdit, "datasetCorpus",'text_corpus'),
            (QTextEdit, "datasetConfig",'text_config'),
            # tokenizer benchmarks
            (QPushButton,'scanHF','scan_for_tokenizers'),
            (QComboBox, "selectTokenizers", 'combo_tokenizers'),            
            (QCheckBox, "includeNSL", 'perform_NSL'),
            (QPushButton, "runBenchmarks", 'run_benchmarks'),
            (QPushButton, "generatePlots", 'generate_plots'),
            (QPlainTextEdit, "tokenizersToBenchmark",'tokenizers_to_bench'),
            ])
        
        self._connect_signals([
            # actions
            ('save_configuration_action', 'triggered', self.save_configuration),   
            ('load_configuration_action', 'triggered', self.load_configuration), 
            ('stop_thread','clicked',self.stop_running_worker),           
            ('combo_tokenizers', 'currentTextChanged', self.update_tokenizers_from_combo),
            ('scan_for_tokenizers', 'clicked', self.find_tokenizers_identifiers),
            ('load_dataset', 'clicked', self.load_and_process_dataset),
            ('analyze_dataset', 'clicked', self.run_dataset_analysis),
            ('run_benchmarks', 'clicked', self.run_tokenizers_benchmark),
            ('generate_plots', 'clicked', self.generate_figures)])
        
        self._auto_connect_settings() 
         

    # [SHOW WINDOW]
    ###########################################################################
    def show(self):        
        self.main_win.show()    
    
    # [HELPERS]
    ###########################################################################
    def connect_update_setting(self, widget, signal_name, config_key, getter=None):
        if getter is None:
            if isinstance(widget, (QCheckBox)):
                getter = widget.isChecked
            elif isinstance(widget, (QSpinBox)):
                getter = widget.value
            elif isinstance(widget, QComboBox):
                getter = widget.currentText
           
        signal = getattr(widget, signal_name)
        signal.connect(partial(self._update_single_setting, config_key, getter))

    #--------------------------------------------------------------------------
    def _update_single_setting(self, config_key, getter, *args):
        value = getter()
        self.config_manager.update_value(config_key, value)

    #--------------------------------------------------------------------------
    def _auto_connect_settings(self):
        connections = [            
            ('use_custom_dataset', 'toggled', 'use_custom_dataset'),
            ('remove_invalid_docs', 'toggled', 'remove_invalid_documents'),
            ('custom_tokenizer', 'toggled', 'include_custom_tokenizer'),
            ('perform_NSL', 'toggled', 'perform_NSL'),
            ('num_documents', 'valueChanged', 'num_documents'),
            ]    

        for attr, signal_name, config_key in connections:
            widget = self.widgets[attr]
            self.connect_update_setting(widget, signal_name, config_key)       

    #--------------------------------------------------------------------------
    def _set_states(self): 
        self.progress_bar = self.main_win.findChild(QProgressBar, "progressBar")
        self.progress_bar.setValue(0)  

    #--------------------------------------------------------------------------
    def _connect_button(self, button_name: str, slot):        
        button = self.main_win.findChild(QPushButton, button_name)
        button.clicked.connect(slot) 

    #--------------------------------------------------------------------------
    def _connect_combo_box(self, combo_name: str, slot):        
        combo = self.main_win.findChild(QComboBox, combo_name)
        combo.currentTextChanged.connect(slot)

    #--------------------------------------------------------------------------
    def _start_thread_worker(self, worker : ThreadWorker, on_finished, on_error, on_interrupted,
                      update_progress=True): 
        if update_progress:       
            self.progress_bar.setValue(0)
            worker.signals.progress.connect(self.progress_bar.setValue)
        worker.signals.finished.connect(on_finished)
        worker.signals.error.connect(on_error)        
        worker.signals.interrupted.connect(on_interrupted)
        self.threadpool.start(worker)

    #--------------------------------------------------------------------------
    def _send_message(self, message): 
        self.main_win.statusBar().showMessage(message)    

    # [SETUP]
    ###########################################################################
    def _setup_configuration(self, widget_defs):
        for cls, name, attr in widget_defs:
            w = self.main_win.findChild(cls, name)
            setattr(self, attr, w)
            self.widgets[attr] = w

    #--------------------------------------------------------------------------
    def _connect_signals(self, connections):
        for attr, signal, slot in connections:
            widget = self.widgets[attr]
            getattr(widget, signal).connect(slot)

    #--------------------------------------------------------------------------
    def _set_widgets_from_configuration(self):
        cfg = self.config_manager.get_configuration()
        for attr, widget in self.widgets.items():
            if attr not in cfg:
                continue
            v = cfg[attr]
            # CheckBox
            if hasattr(widget, "setChecked") and isinstance(v, bool):
                widget.setChecked(v)
            # Numeric widgets (SpinBox/DoubleSpinBox)
            elif hasattr(widget, "setValue") and isinstance(v, (int, float)):
                widget.setValue(v)
            # PlainTextEdit/TextEdit
            elif hasattr(widget, "setPlainText") and isinstance(v, str):
                widget.setPlainText(v)
            # LineEdit (or any widget with setText)
            elif hasattr(widget, "setText") and isinstance(v, str):
                widget.setText(v)
       
    # [SLOT]
    ###########################################################################
    # It's good practice to define methods that act as slots within the class
    # that manages the UI elements. These slots can then call methods on the
    # handler objects. Using @Slot decorator is optional but good practice    
    #--------------------------------------------------------------------------    
    Slot()
    def stop_running_worker(self):
        if self.worker is not None:
            self.worker.stop()       
            self._send_message("Interrupt requested. Waiting for threads to stop...")

    #--------------------------------------------------------------------------
    # [ACTIONS]
    #--------------------------------------------------------------------------
    @Slot()
    def save_configuration(self):
        dialog = SaveConfigDialog(self.main_win)
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_name()
            name = 'default_config' if not name else name            
            self.config_manager.save_configuration_to_json(name)
            self._send_message(f"Configuration [{name}] has been saved")

    #--------------------------------------------------------------------------
    @Slot()
    def load_configuration(self):
        dialog = LoadConfigDialog(self.main_win)
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_selected_config()
            self.config_manager.load_configuration_from_json(name)                
            self._set_widgets_from_configuration()
            self._send_message(f"Loaded configuration [{name}]")

    #--------------------------------------------------------------------------
    # [DATASET]
    #--------------------------------------------------------------------------
    @Slot()
    def load_and_process_dataset(self): 
        if self.worker:            
            message = "A task is currently running, wait for it to finish and then try again"
            QMessageBox.warning(self.main_win, "Application is still busy", message)
            return 
        
        corpus_text = self.main_win.findChild(QTextEdit, "datasetCorpus").toPlainText()
        config_text = self.main_win.findChild(QTextEdit, "datasetConfig").toPlainText()  
        dataset_config = {'corpus': corpus_text.replace('\n', ' ').strip(), 
                          'config': config_text.replace('\n', ' ').strip()} 
        
        # update configuration with the text from the input boxes and reinitialize
        # the loading handler with the new configuration        
        self.config_manager.update_value('DATASET', dataset_config)
        self.configuration = self.config_manager.get_configuration() 
        self.loading_handler = DatasetEvents(
            self.configuration, self.hf_access_token) 
        
        # send message to status bar
        self._send_message(
            f"Downloading dataset {corpus_text} (configuration: {config_text})")        
        # functions that are passed to the worker will be executed in a separate thread
        self.worker = ThreadWorker(self.loading_handler.load_and_process_dataset)

        # start worker and inject signals
        self._start_thread_worker(
            self.worker, on_finished=self.on_dataset_loaded,
            on_error=self.on_error,
            on_interrupted=self.on_task_interrupted)       

    #--------------------------------------------------------------------------
    @Slot()
    def run_dataset_analysis(self):
        if self.worker:            
            message = "A task is currently running, wait for it to finish and then try again"
            QMessageBox.warning(self.main_win, "Application is still busy", message)
            return 
        
        self.configuration = self.config_manager.get_configuration() 
        self.benchmark_handler = BenchmarkEvents(
            self.configuration, self.hf_access_token)  

        # send message to status bar        
        self._send_message("Computing statistics for the selected dataset")       
        # functions that are passed to the worker will be executed in a separate thread
        self.worker = ThreadWorker(self.benchmark_handler.run_dataset_evaluation_pipeline)
           
        # start worker and inject signals
        self._start_thread_worker(
            self.worker, on_finished=self.on_analysis_success,
            on_error=self.on_error,
            on_interrupted=self.on_task_interrupted)            

    #--------------------------------------------------------------------------
    # [TOKENIZERS AND BENCHMARKS]
    #--------------------------------------------------------------------------
    @Slot(str)
    def find_tokenizers_identifiers(self):
        if self.worker:            
            message = "A task is currently running, wait for it to finish and then try again"
            QMessageBox.warning(self.main_win, "Application is still busy", message)
            return 
             
        self.configuration = self.config_manager.get_configuration() 
        self.benchmark_handler = BenchmarkEvents(
            self.configuration, self.hf_access_token)

        # send message to status bar        
        self._send_message("Looking for available tokenizers in Hugging Face")       
        # functions that are passed to the worker will be executed in a separate thread
        self.worker = ThreadWorker(
            self.benchmark_handler.get_tokenizer_identifiers, limit=1000)
          
        # start worker and inject signals
        self._start_thread_worker(
            self.worker, on_finished=self.on_tokenizers_fetched,
            on_error=self.on_error,
            on_interrupted=self.on_task_interrupted)          

    #--------------------------------------------------------------------------
    @Slot(str)
    def update_tokenizers_from_combo(self, text: str):
        tokenizers = self.main_win.findChild(QPlainTextEdit, "tokenizersToBenchmark")  
        existing = set(tokenizers.toPlainText().splitlines())
        if text not in existing:
            tokenizers.appendPlainText(text) 

    #--------------------------------------------------------------------------
    @Slot()
    def run_tokenizers_benchmark(self):
        if self.worker:            
            message = "A task is currently running, wait for it to finish and then try again"
            QMessageBox.warning(self.main_win, "Application is still busy", message)
            return 
        
        tokenizers = self.main_win.findChild(QPlainTextEdit, "tokenizersToBenchmark") 
        tokenizers_name = tokenizers.toPlainText().splitlines()
        if len(tokenizers_name) == 0:   
            logger.warning('No tokenizers selected for benchmarking')         
            return None

        tokenizers_name = [x.replace('\n', ' ').strip() for x in tokenizers_name]
        self.config_manager.update_value('TOKENIZERS', tokenizers_name)

        # initialize the benchmark handler with the current configuration
        self.configuration = self.config_manager.get_configuration() 
        self.benchmark_handler = BenchmarkEvents(
            self.configuration, self.hf_access_token)              

        # send message to status bar
        self._send_message("Running tokenizers benchmark...")          
        # functions that are passed to the worker will be executed in a separate thread
        self.worker = ThreadWorker(self.benchmark_handler.execute_benchmarks)         
        
        # start worker and inject signals
        self._start_thread_worker(
            self.worker, on_finished=self.on_benchmark_finished,
            on_error=self.on_error,
            on_interrupted=self.on_task_interrupted)      

    #--------------------------------------------------------------------------
    @Slot()
    def generate_figures(self):     
        if self.worker:            
            message = "A task is currently running, wait for it to finish and then try again"
            QMessageBox.warning(self.main_win, "Application is still busy", message)
            return 
        
        self.configuration = self.config_manager.get_configuration() 
        self.viewer_handler = VisualizationEnvents(self.configuration)        
        # send message to status bar
        self._send_message("Generating benchmark results figures")   
        # functions that are passed to the worker will be executed in a separate thread
        self.worker = ThreadWorker(self.viewer_handler.visualize_benchmark_results) 

        # start worker and inject signals
        self._start_thread_worker(
            self.worker, on_finished=self.on_plots_generated,
            on_error=self.on_error,
            on_interrupted=self.on_task_interrupted)               

    ###########################################################################
    # [POSITIVE OUTCOME HANDLERS]
    ###########################################################################    
    @Slot(object)
    def on_dataset_loaded(self, name):           
        message = f'Text dataset {name} has been saved into database' 
        logger.info(message)
        self._send_message(message)  
        self.worker = self.worker.cleanup()        

    #--------------------------------------------------------------------------
    @Slot(object)
    def on_analysis_success(self, result):                  
        config = self.config_manager.get_configuration().get('DATASET', {})
        corpus = config.get('corpus', None)  
        config = config.get('config', None)      
        message = f'{corpus} - {config} analysis is finished'
        self._send_message(message)
        logger.info(message)
        self.worker = self.worker.cleanup()

    #--------------------------------------------------------------------------
    @Slot(object)
    def on_tokenizers_fetched(self, identifiers):
        combo = self.main_win.findChild(QComboBox, "selectTokenizers")
        existing = {combo.itemText(i) for i in range(combo.count())}
        for identifier in identifiers:
            if identifier not in existing:
                combo.addItem(identifier)
                  
        self._send_message(f'{len(identifiers)} tokenizer identifiers fetched from HuggingFace')   
        self.worker = self.worker.cleanup()        
    
    #--------------------------------------------------------------------------
    @Slot(object)
    def on_benchmark_finished(self, tokenizers):
        self.tokenizers = tokenizers 
        message = f'{len(tokenizers)} selected tokenizers have been benchmarked'              
        self._send_message(message) 
        logger.info(message)
        self.worker = self.worker.cleanup()  
    
    #--------------------------------------------------------------------------
    @Slot(object)    
    def on_plots_generated(self, figures): 
        self._send_message('Benchmark results plots have been generated')
        self.worker = self.worker.cleanup()    
    
    ###########################################################################   
    # [NEGATIVE OUTCOME HANDLERS]
    ###########################################################################   
    def on_error(self, err_tb):
        exc, tb = err_tb
        logger.error(f"{exc}\n{tb}")
        message = "An error occurred during the operation. Check the logs for details."
        QMessageBox.critical(self.main_win, 'Something went wrong!', message)
        self.progress_bar.setValue(0)      
        self.worker = self.worker.cleanup()  


    ###########################################################################   
    # [INTERRUPTION HANDLERS]
    ###########################################################################     
    def on_task_interrupted(self):         
        self.progress_bar.setValue(0)        
        self._send_message('Current task has been interrupted by user')
        logger.warning('Current task has been interrupted by user')
        self.worker = self.worker.cleanup()
        
    
