from pydantic import BaseModel

class ItemEntry(BaseModel):
    name: str
    amount: int

class RequestBody(BaseModel):
    world_name: str
    items: list[ItemEntry]

#todo: response classes for Endeavor, MaterialList, Material without parent references
class Endeavor(BaseModel):
