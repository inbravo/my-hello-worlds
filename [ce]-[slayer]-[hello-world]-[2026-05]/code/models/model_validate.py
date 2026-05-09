from slayer.client.slayer_client import SlayerClient
from slayer.core.query import SlayerQuery
from slayer.storage.yaml_storage import YAMLStorage
import asyncio

def doc_code():

    # Remote mode (connects to running server)
    client = SlayerClient(url="http://localhost:5143")

    # Or local mode (no server needed)
    # client = SlayerClient(storage=YAMLStorage(base_dir="./slayer_data"))

    # Query data
    query = SlayerQuery(
        source_model="orders",
        measures=["*:count", "revenue:sum"],
        dimensions=["status"],
        limit=10,
    )
    df = client.query_df(query)
    print(df)

# Async version of the validate_model function
async def list_models_async():    

    s = SlayerClient(
        url="http://localhost:5143",
        storage=None
    )
    print(await s.list_models())

# Local validation using YAML storage
def validate_model_yaml(yaml_folder):

    client = SlayerClient(storage=YAMLStorage(base_dir="[ce]-[slayer]-[hello-world]-[2026-05]/code/models"))

    query = {
        "source_model": "capital_position",
        "measures": [
            "latest_cet1_ratio",
            "latest_combined_buffer",
            "buffer_headroom",
            "total_cet1_capital",
            "total_rwa"
        ],
        "dimensions": ["reporting_date", "entity"],
        "limit": 10,
    }

    # Same query API as remote mode
    print(client.query_df(query))


# Run the method
if __name__ == "__main__":
    doc_code()
    # list_models_async()
    # asyncio.run(list_models_async())
    # asyncio.run(validate_model_yaml("capital_position.yaml"))