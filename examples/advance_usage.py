import logging
import time
from underdoc import underdoc_client
from underdoc.model import BatchExecutionMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Construct a new UnderDoc client instance
# By default, it will use the environment variable UNDERDOC_API_KEY
# You can also pass in your own API key to the api_key argument (not recommended)
client = underdoc_client.Client()

# Set the batch execution mode
# Default is parallel mode, set to sequential mode if you want process images one by one
batch_execution_mode = BatchExecutionMode.Sequential
# batch_execution_mode = BatchExecutionMode.Parallel

tic = time.perf_counter()   
response = client.expense_image_batch_extract(file_name_pattern="sample_expense_images/*.*",batch_execution_mode=batch_execution_mode)
toc = time.perf_counter()
logger.info(f"Time taken: {toc - tic:0.4f} seconds")
print(response.model_dump_json(indent=2))
