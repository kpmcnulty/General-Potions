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

        total_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()    
        total_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()

        total_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()    
        total_blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar()

       
        total_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()    
        total_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar()

        for potion in potions_delivered:
            if potion.potion_type == [0, 100, 0, 0]:
                total_green_ml = total_green_ml - (100 * potion.quantity)
                total_green_potions += potion.quantity
            if potion.potion_type == [100, 0, 0, 0]:
                total_red_ml = total_red_ml - (100 * potion.quantity)
                total_red_potions += potion.quantity
            if potion.potion_type == [0, 0, 100, 0]:
                total_blue_ml = total_blue_ml - (100 * potion.quantity)
                total_green_potions += potion.quantity

        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :num_green_ml"), {'num_green_ml': total_green_ml})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_potions = :num_green_potions"), {'num_green_potions': total_green_potions})


        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :num_red_ml"), {'num_red_ml': total_red_ml})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_potions = :num_red_potions"), {'num_red_potions': total_red_potions})


        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = :num_blue_ml"), {'num_blue_ml': total_blue_ml})
        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_potions = :num_blue_potions"), {'num_blue_potions': total_blue_potions})
    #print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"


@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    potions_to_purchase = []
    with db.engine.begin() as connection:
        
        green_ml_response = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
        total_green_ml = green_ml_response.scalar()
        num_green_bottles = total_green_ml // 100

        red_ml_response = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory"))
        total_red_ml = red_ml_response.scalar()
        num_red_bottles = total_red_ml // 100

        blue_ml_response = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory"))
        total_blue_ml = blue_ml_response.scalar()
        num_blue_bottles = total_blue_ml // 100

        
        
        if num_green_bottles > 0:
            potions_to_purchase.append({
                "potion_type": [0, 100, 0, 0],  
                "quantity": num_green_bottles,

            })
        if num_red_bottles > 0:
            potions_to_purchase.append({
                "potion_type": [100, 0, 0, 0],  
                "quantity": num_red_bottles,

            })
        if num_blue_bottles > 0:
            potions_to_purchase.append({
                "potion_type": [0, 0, 100, 0],  
                "quantity": num_blue_bottles,

            })
    return potions_to_purchase 


if __name__ == "__main__":
    print(get_bottle_plan())