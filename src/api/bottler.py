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
       
        potion_rows = connection.execute(sqlalchemy.text(
                """SELECT COUNT(*) FROM potions""")).scalar()
        red_ml = 0
        blue_ml = 0
        green_ml = 0
        dark_ml = 0

        for potion in potions_delivered:
            quantity = potion.quantity

            red_ml += int(((potion.potion_type[0] / 100) * 50) * quantity)
            blue_ml += int(((potion.potion_type[1] / 100) * 50) * quantity)
            green_ml += int(((potion.potion_type[2] / 100) * 50) * quantity)
            dark_ml += int(((potion.potion_type[3] / 100) * 50) * quantity)
            sku = potion_rows + 1
            potion_rows = sku
            connection.execute(
                sqlalchemy.text(
                    "INSERT INTO potions (sku, potion_type, quantity) VALUES (:sku, :potion_type, :quantity)"),
                    [{"sku": sku, "potion_type": potion.potion_type, "quantity": quantity}])
            
        connection.execute(
            sqlalchemy.text("""
                UPDATE globals SET
                red_ml = red_ml - :red_ml,
                green_ml = green_ml - :green_ml,
                blue_ml = blue_ml - :blue_ml,
                dark_ml = dark_ml - :dark_ml
                """),
                [{"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml}])
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
        
        potions = connection.execute(sqlalchemy.text(
            "SELECT * FROM potions"
        )).all()
        potion_capacity = results.potion_capacity
        total_potions = sum(potion.quantity for potion in potions)
        ml_inventory = [results.red_ml, results.green_ml, results.blue_ml, results.dark_ml] 
        potions_to_bottle = []
        sorted_potions = sorted(potions, key=lambda potion: potion.priority)
        for potion in sorted_potions:
            total_potions += potion.quantity
            potion_type = potion.potion_type
            
            print(potion.sku)
            factor_greater = [0,0,0,0] 
            color_mls = [0,0,0,0]

            for i in range(len(potion_type)):
                
                color_mls[i] = (potion_type[i] / 2)
                if color_mls[i] != 0:
                    factor_greater[i] = ml_inventory[i] // color_mls[i]
                else:
                    factor_greater[i] = -1
                print(factor_greater)
            quantity = min(factor for factor in factor_greater if factor != -1)
            print(quantity)

            if (total_potions + quantity) > potion_capacity:
                    quantity = potion_capacity - total_potions
            if quantity >= 1:
                potions_to_bottle.append({
                    "potion_type": potion.sku,
                    "quantity" : quantity
                    })
            total_potions += quantity
            for i in range(len(color_mls)):
                ml_inventory[i] -= (quantity * color_mls[i])

    return potions_to_bottle


if __name__ == "__main__":
    print(get_bottle_plan())