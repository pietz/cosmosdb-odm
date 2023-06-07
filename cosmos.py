import secrets
import json
from typing import Type, TypeVar, Any
from azure.cosmos import CosmosClient, ContainerProxy
from pydantic import BaseModel, Field

T = TypeVar("T", bound="CosmosModel")


def generate_key(n=16):
    abc = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(secrets.choice(abc) for _ in range(n))


class CosmosConnection:
    _instance = None

    def __init__(self, account_url: str, account_key: str, database_name: str):
        if CosmosConnection._instance is not None:
            raise Exception("This class is a singleton!")
        self.client = CosmosClient(account_url, account_key)
        self.database = self.client.get_database_client(database_name)
        CosmosConnection._instance = self

    @staticmethod
    def instance():
        if CosmosConnection._instance is None:
            raise Exception("Cosmos Connection is not initialized.")
        return CosmosConnection._instance

    @classmethod
    def from_connection_string(cls, connection_string: str, database_name: str):
        connection_string = connection_string.rstrip(";")
        connection_params = dict(s.split("=", 1) for s in connection_string.split(";"))
        account_url = connection_params["AccountEndpoint"]
        account_key = connection_params["AccountKey"]
        return cls(account_url, account_key, database_name)


class CosmosModel(BaseModel):
    id: str = Field(default_factory=generate_key)
    _container = None
    _odm_version: int = 1
    _partition_key_field: str = "id"

    @classmethod
    def get_container(cls) -> ContainerProxy:
        if cls._container is None:
            db = CosmosConnection.instance().database
            cls._container = db.get_container_client(cls.__name__)
        return cls._container

    def save(self) -> T:
        container = self.get_container()
        item = container.upsert_item(json.loads(self.json()))
        return self.__class__(**item)

    @classmethod
    def get(cls: Type[T], id: str, pk: str = None) -> T:
        if pk is None and cls._partition_key_field != "id":
            raise Exception("Partition key `pk` is required.")
        container = cls.get_container()
        item = container.read_item(id, id if pk is None else pk)
        return cls(**item)

    def delete(self):
        container = self.get_container()
        partition_key = self._partition_key()
        container.delete_item(self.id, partition_key)

    def _partition_key(self) -> Any:
        return getattr(self, self._partition_key_field)
