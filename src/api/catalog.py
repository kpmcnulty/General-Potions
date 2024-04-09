from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    with db.engine.begin() as connection:
        potions_response = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        total_potions = potions_response.scalar() 
    return [
            {
                "sku": "GREEN_POTIONS",
                "name": "green potion",
                "quantity": total_potions,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            }
        ]
