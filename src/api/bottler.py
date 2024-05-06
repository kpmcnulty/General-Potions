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
            
            
            sku = connection.execute(
                sqlalchemy.text(
                    "SELECT sku from potions WHERE potion_type = :potion_type"),
                [{"potion_type": potion.potion_type}])
            num_transactions = connection.execute(sqlalchemy.text( "SELECT COUNT* FROM potion_transactions")).scalar()
            connection.execute(
                sqlalchemy.text(
                    "INSERT INTO potion_transactions (id, sku, type, delta_potion) VALUES (:id, :sku, :type, :delta_potions)"),
                    [{"id": num_transactions+1, "sku": sku, "type": "Potion bottled", "delta_potions": quantity}])

            num_ml_transactions = connection.execute(sqlalchemy.text( "SELECT COUNT* FROM ml_transactions")).scalar()
            connection.execute(
                sqlalchemy.text("INSERT INTO ml_transactions (id, type, delta_red_ml, delta_green_ml, delta_blue_ml, delta_dark_ml) VALUES (:id, :type, :red_ml, :green_ml, :blue_ml, :dark_ml)"),
                [{"id": num_ml_transactions+1,"type": "Potions bottled", "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml}])
    #print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    return "OK"



@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    potions_to_bottle = []
    with db.engine.begin() as connection:
        potion_capacity = connection.execute(sqlalchemy.text("SELECT potion_capacity FROM globals")).scalar()
        red_ml = connection.execute(sqlalchemy.text("SELECT SUM(delta_red_ml) FROM ml_transactions")).scalar()
        green_ml = connection.execute(sqlalchemy.text("SELECT SUM(delta_green_ml) FROM ml_transactions")).scalar()
        blue_ml = connection.execute(sqlalchemy.text("SELECT SUM(delta_blue_ml) FROM ml_transactions")).scalar()
        dark_ml = connection.execute(sqlalchemy.text("SELECT SUM(delta_dark_ml) FROM ml_transactions")).scalar()

        potions = connection.execute(sqlalchemy.text(
            "SELECT * FROM potions"
        )).all()
        
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT SUM(delta_potion) FROM potion_transactions"
        )).scalar()
        if not total_potions:
            total_potions = 0

        ml_inventory = [red_ml, green_ml, blue_ml, dark_ml] 
   
        for i in range(len(ml_inventory)):
            if not ml_inventory[i]:
                ml_inventory[i] = 0
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
            print(total_potions + quantity)
            print(potion_capacity)
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