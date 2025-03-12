from underdoc import underdoc_client

# Construct a new UnderDoc client instance
# By default, it will use the environment variable UNDERDOC_API_KEY
# You can also pass in your own API key to the api_key argument (not recommended)
client = underdoc_client.Client()

# Extract expense data from an image (png or jpg)
response = client.expense_image_extract(file_name="sample_expense_images/sample-1-receipt-glasses-eng.jpg")

# Print the response
print(response)

# Print the expense data in Json
expense_data = response.receipt_data
print(expense_data.model_dump_json(indent=2))
