from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from src import database as db
import sqlalchemy

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:  
        connection.execute(
            sqlalchemy.text("""
                UPDATE globals SET
                red_ml = 0,
                green_ml = 0,
                blue_ml = 0,
                dark_ml = 0,
                gold = 100,
                potion_capacity = 50,
                ml_capacity = 10000     

                """))
        connection.execute(
            sqlalchemy.text("""
                UPDATE potions SET 
                    quantity = 0"""))
        connection.execute(
            sqlalchemy.text("""
                DELETE FROM processed"""))
        connection.execute(
            sqlalchemy.text("""
                DELETE FROM carts"""))
        connection.execute(
            sqlalchemy.text("""
                DELETE FROM cart_items"""))
    return "OK"

