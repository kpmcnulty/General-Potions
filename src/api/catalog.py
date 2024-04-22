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
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potions")).all()

    catalog = []
    for potion in potions:
        catalog.append(
        {
            "sku": "GREEN_POTION",
            "name": "Green potion",
            "quantity": potion.quantity,
            "price": 50,
            "potion_type": potion.potion_type
        })
    
    return catalog
        
