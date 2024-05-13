from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    offset = (int(search_page) - 1) * 5 
    with db.engine.begin() as connection:
        append_string = """SELECT cart_items.sku, carts.name, cart_items.quantity, to_char(carts.created_at::timestamp, 'MM/DD/YYYY, HH12:MI:SS PM') as created_at
            FROM carts
            JOIN cart_items ON carts.id = cart_items.cart_id"""
    
        print(append_string)
        result = connection.execute(sqlalchemy.text(append_string),[{"customer_name": customer_name, "potion_sku": potion_sku, "sort_col": sort_col,"sort_order": sort_order, "offset": offset}]).all()
       
        search_results = []
        print(result)
        resultid = 0
        for row in result:
            print("row" + str(row))
            resultid += 1
            print(row[0])
            potion_price = connection.execute(sqlalchemy.text(
                    "SELECT price FROM potions WHERE sku = :sku"),
                    {"sku": row[0]}
                ).scalar()
            search_results.append(
                {
                    "line_item_id": resultid,
                    "item_sku": row[0],
                    "customer_name": row[1],
                    "line_item_total": int (row[2]) * potion_price,
                    "timestamp": row[3]
                })
    print(search_results)

    isdescending = (sort_order.lower() == 'desc')
    search_results.sort(key=lambda item: item[sort_col.lower()], reverse=isdescending)
    print(search_results)
    results_page = search_results[offset:offset+5]
    
    if int(search_page) > 1:
        previous_page = str(int(search_page) - 1)
    else:
        previous_page = None
    if len(search_results) >= 5:
        next_page = str(int(search_page) + 1)
    else:
        next_page = None
    

    
    return {
            "previous": previous_page,
            "next": next_page,
            "results": results_page
        }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int



@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"




@router.post("/")
def create_cart(new_cart: Customer):
    with db.engine.begin() as connection:
        num_carts = connection.execute(sqlalchemy.text(
                """SELECT COUNT(*) FROM carts""")).scalar()
        newid = num_carts + 1
        connection.execute(
                sqlalchemy.text(
                    "INSERT INTO carts (id, name) VALUES (:id, :name)"),
                [{"id": newid, "name": new_cart.customer_name}])
    return {"cart_id": newid}


class CartItem(BaseModel):
    quantity: int

    


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text(
                "SELECT * FROM carts WHERE id = :cart_id"),[{"cart_id": cart_id}]).one()
        if cart:
            connection.execute(sqlalchemy.text(
                    """
                    INSERT INTO cart_items (cart_id, sku, quantity) VALUES (:cart_id, :sku, :quantity)
                    """
                ),[{"cart_id": cart_id, "sku": str(item_sku), "quantity": cart_item.quantity}])
        else:
            return "cart_id does not exist"
    return "OK"
    

class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    with db.engine.begin() as connection:
        cart = connection.execute(sqlalchemy.text(
                "SELECT * FROM carts WHERE id = :cart_id"),[{"cart_id": cart_id}]).one()
        if not cart:
            return "cart id does not exist"
        items = connection.execute(sqlalchemy.text(
                "SELECT * FROM cart_items WHERE cart_id = :cart_id"),[{"cart_id": cart_id}])
        goldadded = 0
        potions_bought = 0
        for item in items:
            print(item.sku)
            num_transactions = connection.execute(sqlalchemy.text( "SELECT COUNT(*) FROM potion_transactions")).scalar()
            connection.execute(sqlalchemy.text("""
                           INSERT INTO potion_transactions (id, sku, delta_potion, type) VALUES (:id, :sku, :quantity, :type)
                            """), [{"id": num_transactions+1, "sku": item.sku, "quantity": (-1 * item.quantity), "type": "Cart purchase"}])
            
            
            price = connection.execute(sqlalchemy.text(
                "SELECT price FROM potions WHERE sku = :sku"),[{"sku": item.sku}])
            goldadded += price * item.quantity
            potions_bought += item.quantity
        num_gold_transactions = connection.execute(sqlalchemy.text( "SELECT COUNT(*) FROM money_transactions")).scalar()
        connection.execute(
            sqlalchemy.text("""
                INSERT INTO money_transactions (type, delta_gold) VALUES (:type, :gold)
                """),
                [{"id":num_gold_transactions+1, "type": "cart_checkout", "gold": goldadded}])
    print("potions bought: " +  str(potions_bought)+ " total_gold_paid: " + str(goldadded))
    return {"total_potions_bought": potions_bought, "total_gold_paid": goldadded}
