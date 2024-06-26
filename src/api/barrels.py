from sqlalchemy.exc import IntegrityError
from typing import Literal
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
    def __init__(self, sku, ml_per_barrel: int, potion_type, price, quantity):
        super().__init__(sku=sku, ml_per_barrel=ml_per_barrel, potion_type=potion_type, price=price, quantity=quantity) ##do i need this?

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    print (barrels_delivered)
    with db.engine.begin() as connection:
        connection.execute(
                sqlalchemy.text(
                    "INSERT INTO processed (order_id, type) VALUES (:order_id, 'barrels')"),
                [{"order_id": order_id}])
        #try:
        #    
        #)
        #except IntegrityError as e:
        #    print(f"IntegrityError occurred: {e}")
        #     return "NOT OK"
        gold_paid = 0 
        red_ml = 0
        blue_ml = 0
        green_ml = 0
        dark_ml = 0
        for barrel in barrels_delivered:
                    if barrel.potion_type == [1, 0, 0, 0]:  
                        gold_paid += barrel.price
                        red_ml += barrel.ml_per_barrel

                    elif barrel.potion_type == [0, 1, 0, 0]: 
                        gold_paid += barrel.price
                        green_ml += barrel.ml_per_barrel
                    elif barrel.potion_type == [0, 0, 1, 0]: 
                        gold_paid += barrel.price
                        blue_ml += barrel.ml_per_barrel
                    elif barrel.potion_type == [0, 0, 0, 1]: 
                        gold_paid += barrel.price
                        dark_ml += barrel.ml_per_barrel
                    else:
                        raise Exception("Invalid potion type")
        num_money_transactions = connection.execute(sqlalchemy.text("SELECT COUNT(*) FROM money_transactions")).scalar()
        num_ml_transactions = connection.execute(sqlalchemy.text("SELECT COUNT(*) FROM ml_transactions")).scalar()
        connection.execute(
                sqlalchemy.text("""
                    INSERT INTO ml_transactions (id, type, delta_red_ml, delta_green_ml, delta_blue_ml, delta_dark_ml) VALUES (:id, :type, :red_ml, :green_ml, :blue_ml, :dark_ml)
                    """),
                    [{"id": num_ml_transactions+1,"type": "barrel_purchase", "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml}])
        connection.execute(
                sqlalchemy.text("""
                    INSERT INTO money_transactions (type, delta_gold) VALUES (:type, :gold)
                    """),
                    [{ "type": "barrel_purchase", "gold": (-1 * gold_paid)}])
    print("gold paid: " + str(gold_paid) + " ml bought: "+ str(red_ml + blue_ml + green_ml + dark_ml))
    return "OK"
    
def calculate_barrel_to_purchase(catalog, max_to_spend, potion_type, ml_available):
    #print(max_to_spend)

    possible_barrels = [barrel for barrel in catalog if (barrel.price <= max_to_spend) and (all(barrel.potion_type[i] == potion_type[i] for i in range(4))) and (barrel.ml_per_barrel <= ml_available)]
    
          
    print(possible_barrels)
    if len(possible_barrels) == 0:
        return None 
    possible_barrels.sort(key=lambda x: x.price / x.ml_per_barrel)
    best_value = possible_barrels[0]
    return best_value.sku

@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text(
             """
            SELECT
            ml_threshold,
            ml_capacity
            FROM globals""")).one()
        red_ml = 0
        green_ml = 0
        blue_ml=0
        dark_ml=0
        gold=0
        
        if connection.execute(sqlalchemy.text("SELECT * from ml_transactions")) is not None:
            red_ml = connection.execute(sqlalchemy.text("SELECT SUM(delta_red_ml) FROM ml_transactions")).scalar()
            green_ml = connection.execute(sqlalchemy.text("SELECT SUM(delta_green_ml) FROM ml_transactions")).scalar()
            blue_ml = connection.execute(sqlalchemy.text("SELECT SUM(delta_blue_ml) FROM ml_transactions")).scalar()
            dark_ml = connection.execute(sqlalchemy.text("SELECT SUM(delta_dark_ml) FROM ml_transactions")).scalar()
            gold = connection.execute(sqlalchemy.text("SELECT SUM(delta_gold) FROM money_transactions")).scalar()
    
    ml_inventory = [red_ml, green_ml, blue_ml, dark_ml]       
    for i in range(len(ml_inventory)):
        if not ml_inventory[i]:
            ml_inventory[i] = 0

    ml_capacity = results.ml_capacity
    threshold = results.ml_threshold
    barrel_purchases = []
    current_ml = sum(ml_inventory)
    
     # even budgets unless we are on a tiny budget then we can just buy 1 color
    for i, ml in enumerate(ml_inventory):
         #print("looping"+ str(i)+ str(ml))
         if ml < threshold:
            potion_type = [int(j == i) for j in range(4)]
            print(potion_type)
            print(current_ml)
            print(ml)
            print(min(threshold - ml, ml_capacity - current_ml))
            
            purchase_sku = calculate_barrel_to_purchase(wholesale_catalog, gold/4 if gold > 300 else gold, potion_type, min(threshold - ml, ml_capacity - current_ml))
            print(purchase_sku)
            catalog_entry = None
            if purchase_sku is not None:
                for barrel in wholesale_catalog:  
                        if barrel.sku == purchase_sku:
                            catalog_entry = barrel
            
                   #quantity = min(catalog_entry.quantity, (threshold - current_ml) // catalog_entry.ml_per_barrel)
                   #if quantity > 0:
                quantity = 1 #hardcoded for now, above code isnt working
                barrel_purchase = Barrel(catalog_entry.sku, catalog_entry.ml_per_barrel, catalog_entry.potion_type, catalog_entry.price, quantity)
                barrel_purchases.append(barrel_purchase)
                gold -= barrel_purchase.price * quantity
                current_ml += barrel_purchase.ml_per_barrel * quantity
                
           

    
    print(barrel_purchases)
    return barrel_purchases 