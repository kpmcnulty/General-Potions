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


def get_ml_ratio(ml_inventory):
    total_ml = sum(ml_inventory)
    if total_ml < 100:
        return None
    ratio = [ml / total_ml for ml in ml_inventory]
    
    adjusted_ml = [int(ratio[i] * 100 / sum(ratio)) for i in range(len(ml_inventory))]

    max_ml_index = adjusted_ml.index(max(adjusted_ml))
    while sum(adjusted_ml) < 100:
        adjusted_ml[max_ml_index] += 1  #should be fine since we check if total ml < 100
        
    return adjusted_ml


@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    potions_to_bottle = []
    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text(
                """
                SELECT
                potion_capacity,
                green_ml,
                blue_ml,
                red_ml,
                dark_ml
                FROM globals""")).one()
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT SUM(quantity) FROM potions"
        )).scalar()
        if not total_potions:
            total_potions = 0

        ml_inventory = [results.red_ml, results.green_ml, results.blue_ml, results.dark_ml] 
        total_ml = sum(ml_inventory)
        

        ml_ratio = get_ml_ratio(ml_inventory)
        if not ml_ratio:
            return []

        quantity = 0
        potions_to_bottle = []

        quantities = []
        for inventory, ratio in zip(ml_inventory, ml_ratio):    
            if ratio != 0:
                quantities.append(inventory // ratio)
        quantity = min(quantities)
        if total_potions < results.potion_capacity:
            potions_to_bottle.append(
                {
                    "potion_type": ml_ratio,  
                    "quantity": quantity,

                }
            )
        
    return potions_to_bottle


if __name__ == "__main__":
    print(get_bottle_plan())