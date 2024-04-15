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
        num_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar() 
        num_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar() 
        num_blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar() 

    catalog = []
    #if quantity is 0  return empty list
    if num_green_potions > 0:
        catalog.append(
        {
            "sku": "GREEN_POTION",
            "name": "Green potion",
            "quantity": num_green_potions,
            "price": 50,
            "potion_type": [0, 100, 0, 0]
        })
    if num_red_potions > 0:
        catalog.append(
        {
            "sku": "RED_POTION",
            "name": "Red potion",
            "quantity": num_red_potions,
            "price": 50,
            "potion_type": [100, 0, 0, 0]
        })
    if num_blue_potions > 0:
        catalog.append(
        {
            "sku": "BLUE_POTION",
            "name": "Blue potion",
            "quantity": num_blue_potions,
            "price": 50,
            "potion_type": [0, 0, 100, 0]
        })
    return catalog
        
