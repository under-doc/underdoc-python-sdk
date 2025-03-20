import logging
from underdoc import underdoc_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Construct a new UnderDoc client instance
# By default, it will use the environment variable UNDERDOC_API_KEY
# You can also pass in your own API key to the api_key argument (not recommended)
client = underdoc_client.Client()

# Extract expense data from an image (png or jpg) file
response = client.expense_image_extract(file_name="sample_expense_images/sample-1-receipt-glasses-eng.jpg")

# Print the response
print(response)

# Print the expense data in Json
if response:
    expense_data = response.receipt_data
    print(expense_data.model_dump_json(indent=2))

# Extract expense data from an image (png or jpg) url
response = client.expense_image_extract(image_url="https://www.underdoc.io/images/receipt-8-tea-restaurant-chin.png")

# Print the response
print(response)

# Print the expense data in Json
if response:
    expense_data = response.receipt_data
    print(expense_data.model_dump_json(indent=2))
