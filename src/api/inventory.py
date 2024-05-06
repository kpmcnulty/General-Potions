from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        ##todo
        ##get num of red mls
        
        red_ml = 0
        green_ml = 0
        blue_ml=0
        dark_ml=0
        gold=0

        if connection.execute("SELECT * from ml_transactions"):
            red_ml = connection.execute("SELECT SUM(delta_red_ml) FROM ml_transactions").scalar()
            green_ml = connection.execute("SELECT SUM(delta_green_ml) FROM ml_transactions").scalar()
            blue_ml = connection.execute("SELECT SUM(delta_blue_ml) FROM ml_transactions").scalar()
            dark_ml = connection.execute("SELECT SUM(delta_dark_ml) FROM ml_transactions").scalar()
            gold = connection.execute("SELECT SUM(delta_gold) FROM money_transactions").scalar()
      

       
        total_ml = sum([red_ml, green_ml, blue_ml, dark_ml]) 
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT SUM(delta_potion) FROM potions_transactions"
        )).scalar()
        if not total_potions:
            total_potions = 0
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        results = connection.execute(sqlalchemy.text(
                """
                SELECT
                ml_capacity,
                potion_capacity,
                FROM globals""")).one()
        red_ml = connection.execute("SELECT SUM(delta_red_ml) FROM ml_transactions").scalar()
        green_ml = connection.execute("SELECT SUM(delta_green_ml) FROM ml_transactions").scalar()
        blue_ml = connection.execute("SELECT SUM(delta_blue_ml) FROM ml_transactions").scalar()
        dark_ml = connection.execute("SELECT SUM(delta_dark_ml) FROM ml_transactions").scalar()
        gold = connection.execute("SELECT SUM(delta_gold) FROM money_transactions").scalar()

        total_potions = connection.execute(sqlalchemy.text(
            "SELECT SUM(delta_potion) FROM potion_transacions"
        )).scalar()
        
        if not total_potions:
            total_potions = 0
    potion_units = 0
    ml_units = 0
    if (total_potions / results.potion_capacity) > .9:
        if gold >= 1000:
            potion_units += 1
    total_ml = sum([red_ml, green_ml, blue_ml, dark_ml]) 
    if (total_ml / results.ml_capacity) > .9:
        if gold >= 1000:
            ml_units += 1
    return {
        "potion_capacity": potion_units,
        "ml_capacity": ml_units
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        gold_cost = (capacity_purchase.potion_capacity + capacity_purchase.ml_capacity) * 1000

        # Update the gold, potion capacity, and ml capacity in the database
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory
                SET 
                    potion_capacity = potion_capacity + :potion_capacity,
                    ml_capacity = ml_capacity + :ml_capacity
                """
            ),
            {"potion_capacity": capacity_purchase.potion_capacity, "ml_capacity": capacity_purchase.ml_capacity},
        )
        num_transactions = connection.execute(sqlalchemy.text(
            "SELECT COUNT* FROM money_transactions"
        )).scalar()
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO money_transactions (id, type, delta_gold) VALUES (:id, :type, :delta_gold)
                """
            ),
            {"id": (num_transactions+1), "type": "capacity purchase", "delta_gold": (-1 * gold_cost)},
            )
        
        
    return "OK"
