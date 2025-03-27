import logging
import time
from underdoc import underdoc_client
from underdoc.model import S3Object, BatchExecutionMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Construct a new UnderDoc client instance
# By default, it will use the environment variable UNDERDOC_API_KEY
# You can also pass in your own API key to the api_key argument (not recommended)
client = underdoc_client.Client()

def s3_single_file(bucket_name: str, object_key: str):
    # Extract expense data from S3 bucket and object key
    tic = time.perf_counter()

    # Construct the S3Object
    # Make sure that there exist AWS credentials in the environment variables that can access the bucket
    s3_object = S3Object(
        bucket_name=bucket_name,
        object_key=object_key
    )

    response = client.expense_image_extract(s3_object=s3_object)
    toc = time.perf_counter()

    logger.info(f"Time taken: {toc - tic:0.4f} seconds")

    # Print the expense data in Json
    if response:
        expense_data = response.receipt_data
        print(expense_data.model_dump_json(indent=2))

def s3_batch_extract(bucket_name: str, batch_execution_mode: BatchExecutionMode = BatchExecutionMode.Parallel):
    # Extract expense data from all files in a S3 bucket
    tic = time.perf_counter()

    response = client.expense_image_batch_extract(s3_bucket_name=bucket_name, batch_execution_mode=batch_execution_mode)

    toc = time.perf_counter()

    logger.info(f"Time taken: {toc - tic:0.4f} seconds")

    print(response.model_dump_json(indent=2))

if __name__ == "__main__":
    # Procoess a single file in a S3 bucket (uncomment to process a single file)
    # Replace the bucket_name and object_key with the bucket name and object key of the image you want to extract expense data from
    # s3_single_file(bucket_name="underdoc-sample-expense-images", object_key="receipt-9-glasses-eng.jpg")

    # Process all files in a S3 bucket (sequential mode) (uncomment to process all files in a S3 bucket)
    # s3_batch_extract(bucket_name="underdoc-sample-expense-images", batch_execution_mode=BatchExecutionMode.Sequential)

    # Process all files in a S3 bucket (parallel mode) (uncomment to process all files in a S3 bucket)
    s3_batch_extract(bucket_name="underdoc-sample-expense-images")
