from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List

class ImageFormat(str, Enum):
    jpeg = "jpeg"
    png = "png"

class ExpenseExtractionRequest(BaseModel):
    image_format: ImageFormat = Field(..., description="Image format (e.g. jpeg, png)")
    image_data: str = Field(..., description="Base64 encoded image data")

class ExpenseImageType(str, Enum):
    Receipt = "Receipt"
    Invoice = "Invoice" 
    Others = "Others"

class ExpenseItem(BaseModel):
    name: Optional[str] = Field(description="The name of the item")
    quantity: Optional[float] = Field(description="The quantity of the item")
    unit_price: Optional[float] = Field(description="The unit price of the item")
    subtotal: Optional[float] = Field(description="The subtotal of the item")

class Expense(BaseModel):
    shop_name: Optional[str] = Field(description="The name of the shop")
    shop_address: Optional[str] = Field(description="The address of the shop")
    date: Optional[str] = Field(description="The date of the expense")
    expense_category: Optional[str] = Field(description="The category of the expense")
    currency: Optional[str] = Field(description="The currency of the expense")
    total_amount: Optional[float] = Field(description="The total amount of the expense")
    items: Optional[List[ExpenseItem]] = Field(description="The items of the expense")

class ExpenseData(BaseModel):
    image_type: ExpenseImageType
    expense: Optional[Expense] = Field(description="The expense details")

class ExpenseExtractionResponse(BaseModel):
    receipt_data: ExpenseData = Field(..., description="Extracted esxpense data")

class ExpenseDataWithSource(BaseModel):
    source_file_name: str = Field(..., description="The source file path")
    expense_data: ExpenseData = Field(..., description="Extracted expense data")

class ExpenseExtractionBatchResponse(BaseModel):
    expense_data_list: List[ExpenseDataWithSource] = Field(..., description="List of extracted expense data with source file path")

class BatchExecutionMode(str, Enum):
    Sequential = "Sequential"
    Parallel = "Parallel"
