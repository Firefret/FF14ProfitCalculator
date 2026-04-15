# --- Requests ---
from pydantic import BaseModel, ConfigDict


class ItemEntry(BaseModel):
    name: str
    amount: int
    model_config = ConfigDict(title="request.ItemEntry")

class Body(BaseModel):
    world_name: str
    items: list[ItemEntry]
    model_config = ConfigDict(title="request.Body")