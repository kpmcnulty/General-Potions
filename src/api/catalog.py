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
    counter = 0
    for potion in potions:
        try:
            quantity = connection.execute(sqlalchemy.text(
                "SELECT SUM(delta_potion) FROM potion_transacions WHERE sku = :sku",
                {"sku": potion.sku},
            )).scalar()
        except Exception:
            quantity = 0
        if quantity == None:
            quantity = 0
        if potion.quantity > 0 and counter < 6:
            catalog.append(
            {
                "sku": potion.sku,
                "name": potion.name,
                "quantity": quantity, #TODO: LEDGERIZE
                "price": potion.price, 
                "potion_type": potion.potion_type
            })
            counter += 1
    
    return catalog
        
