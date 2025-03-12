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

    def _get_request_from_file_name(self,
                                    file_name: str) -> ExpenseExtractionRequest:
        """Get a request from a file name.
        
        """
        logger.info(f"Getting request from file name: {file_name}")

        # Read the image file
        with open(file_name, "rb") as image_file:
            # Get the image type
            file_extension = file_name.split(".")[-1]
            if file_extension in ['jpg', 'jpeg']:
                image_format = ImageFormat.jpeg
            elif file_extension == 'png':
                image_format = ImageFormat.png
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")

            image_data = image_file.read()

        # Encode the image data
        image_data_encoded = base64.b64encode(image_data).decode("utf-8")

        # Return the request
        return ExpenseExtractionRequest(
            image_format=image_format,
            image_data=image_data_encoded
        )

    def expense_image_extract(self,
                              file_name: str | None) -> ExpenseExtractionResponse:
        """Extract expense data from an image.

        Provide one of the following:
        - `file_name`: The path to the image file.
        """

        # Handle file name
        if file_name:
            try:
                request = self._get_request_from_file_name(file_name)
            except ValueError as e:
                raise UnderDocException(e)
            
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
