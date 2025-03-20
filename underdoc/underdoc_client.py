from .config import Settings
from .model import ExpenseExtractionRequest, ExpenseExtractionResponse, ImageFormat
import logging
import base64
import httpx
from .exceptions import UnderDocException

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

    def expense_image_extract(self,
                              file_name: str | None = None,
                              image_url: str | None = None) -> ExpenseExtractionResponse:
        """Extract expense data from an image.

        Provide one of the following:
        - `file_name`: The path to the image file.
        """

        if file_name is None and image_url is None:
            raise ValueError("Either file_name or image_url must be provided.")

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
