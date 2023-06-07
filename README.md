# cosmosdb-odm
I'm not a big fan of the CosmosDB Python SDK syntax and decided to write a simple ODM wrapper for it. It runs on top of Pydantic.

## Example

```python
from cosmos import CosmosConnection, CosmosModel

class Items(CosmosModel):
    name: str
    age: int
    is_active: bool

# Creates a singleton that will be used in the background
cosmos_conn = CosmosConnection.from_connection_string("CONNECTION_STR", "DB_NAME")

# Read from collection "Items"
item = Items.get(id="ID")

# Read if PK != ID
item = Items.get(id="ID", pk="PARTITION_KEY")

# Random ID is generated in the background
item = Items(name="Pietz", age=33, is_active=True)
print(item.id)

# Create & Update (Upsert)
item.save()

# Delete
item.delete()

```