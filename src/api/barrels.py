from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    
    with db.engine.begin() as connection:
        
        for barrel in barrels_delivered:
                gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
                if gold >= (barrel.price * barrel.quantity):
                    new_gold = gold - (barrel.price * barrel.quantity)
                    connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :gold"), {'gold': new_gold})

                    #green
                    if barrel.potion_type == [0, 1, 0, 0]: 
                        total_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
                        new_total_ml = total_ml + barrel.ml_per_barrel * barrel.quantity
                        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :num_green_ml"), {'num_green_ml': new_total_ml})
                    #red
                    elif barrel.potion_type == [1, 0, 0, 0]:  
                        total_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
                        new_total_ml = total_ml + barrel.ml_per_barrel * barrel.quantity
                        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_red_ml = :num_red_ml"), {'num_red_ml': new_total_ml})
                    #blue
                    elif barrel.potion_type == [0, 0, 1, 0]: 
                        total_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
                        new_total_ml = total_ml + barrel.ml_per_barrel * barrel.quantity
                        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_blue_ml = :num_blue_ml"), {'num_blue_ml': new_total_ml})
    return "OK"
    

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    with db.engine.begin() as connection:
        print(wholesale_catalog)
        sql_to_execute = "SELECT gold FROM global_inventory"
        result = connection.execute(sqlalchemy.text(sql_to_execute))
        gold = result.scalar()
        to_purchase = []
        for barrel in wholesale_catalog:
            potion_type = barrel.potion_type 
            sku = barrel.sku
            #just going to buy in catalog order if less than 10 potions for now, 
            if gold >= barrel.price:
                if potion_type == [0,1,0,0]:
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
                elif potion_type == [1,0,0,0]:
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar()
                elif potion_type == [0,0,1,0]:
                    num_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar()

                max_quantity = min(barrel.quantity, (gold // barrel.price)) 

                #print("SKU: "+sku+" price: " + barrel.price+ " max_quantity = " + max_quantity)

                if num_potions <= 10 and max_quantity > 0:
                    target_quantity =  ((10 - num_potions) * 100 ) // barrel.ml_per_barrel + 1 # buy just enough to get us over 10 potions
                    tobuy = min(max_quantity, target_quantity)
                    gold -= (barrel.price * tobuy) #
                    ml = barrel.ml_per_barrel
                    price = barrel.price
                    to_purchase.append({
                        "sku": sku,
                        "ml_per_barrel": ml,
                        "potion_type": potion_type,
                        "price": price,
                        "quantity":  tobuy
                    })
        return to_purchase

