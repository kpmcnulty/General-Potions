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
        #output=""
        for barrel in barrels_delivered:
                if barrel.potion_type == [0,100,0, 0]: # temp value fpr 100% green
                    gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory"))
                    gold = gold.scalar()

                    if gold >= barrel.price:
                        new_gold = gold - barrel.price
                        
                        connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = :gold"), {'gold': new_gold})

                        ml_query = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
                        total_ml = ml_query.scalar()
                        new_total_ml = total_ml + (barrel.ml_per_barrel * barrel.quantity)

                        connection.execute(sqlalchemy.text("UPDATE global_inventory SET num_green_ml = :num_green_ml"), {'num_green_ml': new_total_ml})
                        #output = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory"))
    return "OK"
    

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    for barrel in wholesale_catalog:
        with db.engine.begin() as connection:
            potion_type = barrel.potion_type #not needed yet, we only have green poitions
            sku = barrel.sku
            price = barrel.price

            sql_to_execute = "SELECT gold FROM global_inventory"
            result = connection.execute(sqlalchemy.text(sql_to_execute))
            gold = result.scalar()

            #sql_to_execute = f"SELECT num_green_potions FROM global_inventory WHERE potion_type = {potion_type}" #not needed yet
            sql_to_execute = "SELECT num_green_potions FROM global_inventory"
            quantity = connection.execute(sqlalchemy.text(sql_to_execute))
            num_potions = quantity.fetchone()[0]
            to_purchase = []
            if num_potions <= 10 and gold >= price:
                gold -= price #just for checking in loop if theres multiple kinds of buckets, actual gold will be changed in deliver
                to_purchase.append({
                    "sku": sku,
                    "quantity": 1
                })
        return to_purchase

