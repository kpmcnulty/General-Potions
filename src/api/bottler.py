from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    with db.engine.begin() as connection:
        ml_response = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        total_ml = ml_response.scalar()    
        potions_response = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory"))
        total_potions = potions_response.scalar()
        for potion in potions_delivered:

            total_ml = total_ml - 100 #change to use colors later based on potion_type
            total_potions += potion.quantity
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :num_green_ml"), {'num_green_ml': total_ml})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :num_green_potions"), {'num_green_potions': total_potions})
    #print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    bottled_potions = []
    with db.engine.begin() as connection:
        
        ml_response = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        total_ml = ml_response.scalar()
        num_bottles = total_ml // 100
        
        if num_bottles > 0:
            bottled_potions.append({
                "potion_type": [0, 1, 0, 0],  # 100% green potion for now
                "quantity": num_bottles,

            })
    return bottled_potions


if __name__ == "__main__":
    print(get_bottle_plan())