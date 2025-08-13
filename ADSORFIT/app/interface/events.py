import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg

from TokenBenchy.app.utils.data.serializer import DataSerializer
from TokenBenchy.app.utils.downloads import DatasetManager, TokenizersDownloadManager
from TokenBenchy.app.utils.benchmarks import BenchmarkTokenizers, VisualizeBenchmarkResults
from TokenBenchy.app.utils.data.processing import ProcessDataset
from TokenBenchy.app.interface.workers import check_thread_status, update_progress_callback
from TokenBenchy.app.logger import logger



###############################################################################
class DatasetEvents:

    def __init__(self, configuration, hf_access_token):
        self.configuration = configuration
        self.hf_access_token = hf_access_token           
           
    #--------------------------------------------------------------------------
    def load_and_process_dataset(self, worker=None, progress_callback=None):
        manager = DatasetManager(self.configuration, self.hf_access_token) 
        dataset_name = manager.get_dataset_name() 
        logger.info(f'Downloading and saving dataset: {dataset_name}')    
        dataset = manager.dataset_download()

        # check thread for interruption 
        check_thread_status(worker)
        update_progress_callback(1, 3, progress_callback)
        
        # process text dataset to remove invalid documents
        processor = ProcessDataset(self.configuration, dataset) 
        documents = processor.process_text_dataset() 
        n_removed_docs = processor.num_documents - len(documents)
        logger.info(f'Total number of documents: {processor.num_documents}')
        logger.info(f'Number of filtered documents: {len(documents)} ({n_removed_docs} removed)')

        # check thread for interruption 
        check_thread_status(worker)
        update_progress_callback(2, 3, progress_callback)

        # create dataframe for text dataset
        text_dataset = pd.DataFrame(
            {'dataset_name': [dataset_name] * len(documents),
             'text': documents,
             'words_count' : [np.nan] * len(documents),
             'AVG_words_length': [np.nan] * len(documents),
             'STD_words_length': [np.nan] * len(documents)})
        
        # serialize text dataset by saving it into database
        serializer = DataSerializer(self.configuration)        
        serializer.save_text_dataset(text_dataset)  

        # check thread for interruption         
        update_progress_callback(3, 3, progress_callback)

        return dataset_name
        


###############################################################################
class BenchmarkEvents:

    def __init__(self, configuration, hf_access_token): 
        self.configuration = configuration    
        self.hf_access_token = hf_access_token                                   
           
    #--------------------------------------------------------------------------
    def run_dataset_evaluation_pipeline(self, progress_callback=None, worker=None):        
        benchmarker = BenchmarkTokenizers(self.configuration)
        benchmarker.calculate_text_statistics(
            progress_callback=progress_callback, worker=worker)         
    
    #--------------------------------------------------------------------------
    def get_tokenizer_identifiers(self, limit=1000, worker=None):
        downloader = TokenizersDownloadManager(self.configuration, self.hf_access_token)
        identifiers = downloader.get_tokenizer_identifiers(limit=limit, worker=worker)

        return identifiers
    
    #--------------------------------------------------------------------------
    def execute_benchmarks(self, progress_callback=None, worker=None):
        benchmarker = BenchmarkTokenizers(self.configuration)
        downloader = TokenizersDownloadManager(self.configuration, self.hf_access_token)
        tokenizers = downloader.tokenizer_download(worker=worker)
        results = benchmarker.run_tokenizer_benchmarks(
           tokenizers, progress_callback=progress_callback, worker=worker) 

        return tokenizers     


###############################################################################
class VisualizationEnvents:

    def __init__(self, configuration : dict):
        self.configuration = configuration 
        self.DPI = configuration.get('image_resolution', 400)

    #--------------------------------------------------------------------------
    def visualize_benchmark_results(self, worker=None, progress_callback=None):
        visualizer = VisualizeBenchmarkResults(self.configuration)
        figures = []      
        # 1. generate plot of different vocabulary sizes
        figures.append(visualizer.plot_vocabulary_size())
        check_thread_status(worker)
        update_progress_callback(1, 3, progress_callback)
        # 2. generate plot of token length distribution
        figures.extend(visualizer.plot_tokens_length_distribution())
        check_thread_status(worker)
        update_progress_callback(2, 3, progress_callback)        
        # 2. generate plot of words versus subwords
        figures.append(visualizer.plot_subwords_vs_words())    
        update_progress_callback(3, 3, progress_callback)        

        return figures  
  