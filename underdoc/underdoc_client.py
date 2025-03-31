from .config import Settings
from .model import (
    ExpenseExtractionRequest, 
    ExpenseExtractionResponse, 
    ImageFormat, 
    ExpenseExtractionBatchResponse, 
    ExpenseDataWithSource, 
    BatchExecutionMode,
    S3Object
)
import logging
import base64
import httpx
import glob
import boto3
from .exceptions import UnderDocException
import ray

logger = logging.getLogger(__name__)

class Client:
    def __init__(self, 
                 api_key: str | None = None) -> None:
        """Construct a new UnderDoc client instance.

        This automatically infers the following arguments from their corresponding environment variables if they are not provided:
        - `api_key` from `UNDERDOC_API_KEY`
        """
        self.settings = Settings()

        # Check if api_key is provided
        if api_key is None:
            api_key = self.settings.underdoc_api_key

        # Check if api_key is provided
        if api_key is None:
            raise ValueError("api_key is required. Either provide it as an argument or set the UNDERDOC_API_KEY environment variable.")
        
        self.api_key = api_key
        self.api_endpoint = self.settings.underdoc_api_endpoint

        logger.info("UnderDoc client initialized successfully")

    def _get_image_format(self, file_path: str) -> ImageFormat:
        """Get the image format from a file path.

        Args:
            file_path: The path to the image file.

        Returns:
            The image format (jpeg or png).

        Raises:
            ValueError: If the file format is not supported.
        """
        file_extension = file_path.split(".")[-1]
        
        if file_extension in ['jpg', 'jpeg']:
            return ImageFormat.jpeg
        elif file_extension == 'png':
            return ImageFormat.png
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    def _get_request_from_file_name(self,
                                    file_name: str) -> ExpenseExtractionRequest:
        """Get a request from a file name.
        
        Args:
            file_name: The path to the image file.

        Returns:
            An ExpenseExtractionRequest object containing the image format and base64 encoded image data.

        Raises:
            ValueError: If the image format is not supported.
            FileNotFoundError: If the file does not exist.
            IOError: If there is an error reading the file.
        """
        logger.info(f"Getting request from file name: {file_name}")

        try:
            # Read the image file
            with open(file_name, "rb") as image_file:
                # Get the image type
                image_format = self._get_image_format(file_name)

                image_data = image_file.read()

            # Encode the image data
            image_data_encoded = base64.b64encode(image_data).decode("utf-8")
        except Exception as e:
            logger.error(F"Error reading file {file_name}: {e}")
            return None

        # Return the request
        return ExpenseExtractionRequest(
            image_format=image_format,
            image_data=image_data_encoded
        )
    
    def _get_request_from_image_url(self,
                                    image_url: str) -> ExpenseExtractionRequest:
        """Get a request from an image url.
        Args:
            image_url: The url of the image.

        Returns:
            An ExpenseExtractionRequest object containing the image format and base64 encoded image data.

        Raises:
            ValueError: If the image format is not supported.
            httpx.RequestError: If there is an error making the HTTP request.
            httpx.HTTPStatusError: If the HTTP request returns a 4xx or 5xx status code.
        """
        logger.info(f"Getting request from image url: {image_url}")

        try:
            image_format = self._get_image_format(image_url)

            with httpx.Client() as client:
                response = client.get(image_url)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                
                image_data = response.content
        except httpx.RequestError as e:
            print(f"Request error: {e}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"HTTP status error: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

        # Encode the image data
        image_data_encoded = base64.b64encode(image_data).decode("utf-8")

        # Return the request
        return ExpenseExtractionRequest(
            image_format=image_format,
            image_data=image_data_encoded
        )
    
    def _get_request_from_s3_object(self,
                                    s3_object: S3Object) -> ExpenseExtractionRequest:
        """Get a request from an s3 object.
        """
        logger.info(f"Getting request from s3 object: {s3_object}")
        s3 = boto3.client('s3')

        try:
            image_format = self._get_image_format(s3_object.object_key)

            response = s3.get_object(Bucket=s3_object.bucket_name, Key=s3_object.object_key)
            image_data = response['Body'].read()
        except Exception as e:
            logger.error(f"Error getting object from s3: {e}")
            return None

        # Encode the image data
        image_data_encoded = base64.b64encode(image_data).decode("utf-8")

        return ExpenseExtractionRequest(
            image_format=image_format,
            image_data=image_data_encoded
        )
    
    def _get_files_from_s3_bucket(self, s3_bucket_name: str) -> list[str]:
        """Get all files from an s3 bucket.
        """
        s3 = boto3.client('s3')
        response = s3.list_objects_v2(Bucket=s3_bucket_name)
        return [obj['Key'] for obj in response['Contents']]

    def expense_image_extract(self,
                              file_name: str | None = None,
                              image_url: str | None = None,
                              s3_object: S3Object | None = None) -> ExpenseExtractionResponse:
        """Extract expense data from an image.

        Provide one of the following:
        - `file_name`: The path to the image file.
        - `image_url`: The url of the image.
        - `s3_object`: The s3 object containing the image.
        """

        if file_name is None and image_url is None and s3_object is None:
            raise ValueError("Either file_name or image_url or s3_object must be provided.")

        # Handle file name
        if file_name:
            try:
                request = self._get_request_from_file_name(file_name)
            except ValueError as e:
                raise UnderDocException(e)
        elif image_url:
            try:
                request = self._get_request_from_image_url(image_url)
            except ValueError as e:
                raise UnderDocException(e)
        elif s3_object:
            try:
                request = self._get_request_from_s3_object(s3_object)
            except ValueError as e:
                raise UnderDocException(e)
            
        if not request:
            logger.error("Failed to create request from file name or image url")
            return None
            
        # Send request for expense extraction
        response = httpx.post(
            f"{self.api_endpoint}/expenses/extract",
            headers={"UNDERDOC_API_KEY": self.api_key},
            json=request.model_dump(),
            timeout=60.0
        )

        # Check if the request was successful
        if response.status_code != 200:
            raise UnderDocException(response.text)
        
        # Parse the response
        extracted_response = ExpenseExtractionResponse.model_validate_json(response.text)

        return extracted_response
    
    @ray.remote
    def _expense_image_extract_parallel(self,
                              file_name: str | None = None,
                              image_url: str | None = None,
                              s3_object: S3Object | None = None) -> tuple[str, ExpenseExtractionResponse]:
        """Extract expense data from an image in parallel mode.

        Provide one of the following:
        - `file_name`: The path to the image file.
        - `image_url`: The url of the image.
        - `s3_object`: The s3 object containing the image.
        """

        if file_name is None and image_url is None and s3_object is None:
            raise ValueError("Either file_name or image_url or s3_object must be provided.")

        # Handle file name
        if file_name:
            try:
                source_file_name = file_name
                request = self._get_request_from_file_name(file_name)
            except ValueError as e:
                raise UnderDocException(e)
        elif image_url:
            try:
                source_file_name = image_url
                request = self._get_request_from_image_url(image_url)
            except ValueError as e:
                raise UnderDocException(e)
        elif s3_object:
            try:
                source_file_name = s3_object.object_key
                request = self._get_request_from_s3_object(s3_object)
            except ValueError as e:
                raise UnderDocException(e)
            
        if not request:
            logger.error("Failed to create request from file name or image url")
            return None
            
        # Send request for expense extraction
        response = httpx.post(
            f"{self.api_endpoint}/expenses/extract",
            headers={"UNDERDOC_API_KEY": self.api_key},
            json=request.model_dump(),
            timeout=3600.0
        )

        # Check if the request was successful
        if response.status_code != 200:
            raise UnderDocException(response.text)
        
        # Parse the response
        extracted_response = ExpenseExtractionResponse.model_validate_json(response.text)

        return source_file_name, extracted_response

    def expense_image_batch_extract(self,
                                    file_name_pattern: str | None = None,
                                    s3_bucket_name: str | None = None,
                                    batch_execution_mode: BatchExecutionMode = BatchExecutionMode.Parallel) -> ExpenseExtractionBatchResponse:
        """Extract expense data from multiple images.
        Extract expense data from multiple images matching a file pattern.

        Args:
            file_name_pattern: A glob pattern to match image files (e.g. "*.jpg", "receipts/*.png")
            s3_bucket_name: The name of the s3 bucket containing the images.
            batch_execution_mode: The execution mode, either Sequential or Parallel. Defaults to Parallel.

        Returns:
            An ExpenseExtractionBatchResponse containing a list of extracted expense data with their source file paths.

        Raises:
            ValueError: If file_name_pattern is not provided
            UnderDocException: If there is an error extracting data from any image
        """

        if file_name_pattern is None and s3_bucket_name is None:
            raise ValueError("file_name_pattern or s3_bucket_name is required.")

        if file_name_pattern:
            logger.info(f"Extracting expense data from file pattern: {file_name_pattern}, execution mode: {batch_execution_mode}")
        else:
            logger.info(f"Extracting expense data from s3 bucket: {s3_bucket_name}, execution mode: {batch_execution_mode}")

        expense_data_list = []

        if file_name_pattern:
            # Get all files matching the pattern
            file_names = glob.glob(file_name_pattern)
        else:
            # Get all files from the s3 bucket
            file_names = self._get_files_from_s3_bucket(s3_bucket_name)
        
        if batch_execution_mode == BatchExecutionMode.Parallel:
            ray.init()
            
            if file_name_pattern:
                response_futures = [self._expense_image_extract_parallel.remote(self, file_name=file_name) for file_name in file_names]
            else:
                response_futures = [self._expense_image_extract_parallel.remote(self, s3_object=S3Object(bucket_name=s3_bucket_name, object_key=file_name)) for file_name in file_names]
        
            responses = ray.get(response_futures)

            for response in responses:
                if response:
                    expense_data_list.append(ExpenseDataWithSource(
                        source_file_name=response[0],
                        expense_data=response[1].receipt_data
                    ))
        else:
            for file_name in file_names:
                if file_name_pattern:
                    response = self.expense_image_extract(file_name=file_name)
                else:
                    response = self.expense_image_extract(s3_object=S3Object(bucket_name=s3_bucket_name, object_key=file_name))
                if response:
                    expense_data_list.append(ExpenseDataWithSource(
                        source_file_name=file_name,
                        expense_data=response.receipt_data
                    ))

        logger.info(f"Extracted {len(expense_data_list)} expense data from {len(file_names)} images")

        return ExpenseExtractionBatchResponse(expense_data_list=expense_data_list)
