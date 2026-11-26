from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(__file__).resolve().parent / "menuflow.db"
app = FastAPI(title="MenuFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS restaurants (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, owner TEXT NOT NULL,
            email TEXT NOT NULL, phone TEXT DEFAULT '', address TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Pendente', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS customer_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
            phone TEXT DEFAULT '', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, category TEXT NOT NULL DEFAULT 'Geral',
            price REAL NOT NULL DEFAULT 0, description TEXT DEFAULT '',
            ingredients TEXT DEFAULT '', prep_minutes INTEGER DEFAULT 0,
            available INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, category TEXT DEFAULT 'Geral',
            quantity REAL NOT NULL DEFAULT 0, minimum REAL NOT NULL DEFAULT 0,
            expiry TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT, stock_id INTEGER NOT NULL,
            kind TEXT NOT NULL, quantity REAL NOT NULL, note TEXT DEFAULT '', created_at TEXT NOT NULL,
            FOREIGN KEY(stock_id) REFERENCES stock(id)
        );
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'Atendente',
            phone TEXT DEFAULT '', shift TEXT DEFAULT 'Integral',
            hire_date TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Ativo'
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL DEFAULT 'Cliente balcão',
            items TEXT NOT NULL DEFAULT 'Pedido',
            total REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Aguardando',
            prep_minutes INTEGER NOT NULL DEFAULT 15,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER, customer TEXT NOT NULL DEFAULT 'Cliente balcão',
            amount REAL NOT NULL DEFAULT 0, method TEXT NOT NULL DEFAULT 'PIX',
            status TEXT NOT NULL DEFAULT 'Pago', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL, amount REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """)
        if con.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            con.executemany("""INSERT INTO products(name,category,price,description,ingredients,prep_minutes,available)
                VALUES(?,?,?,?,?,?,?)""", [
                ("Hambúrguer da Casa","Lanches",28.90,"Pão, carne e queijo","Pão, carne, queijo",15,1),
                ("Batata frita","Acompanhamentos",12.00,"Porção crocante","Batata, sal",8,1),
                ("Suco de laranja","Bebidas",8.50,"Suco natural 300ml","Laranja",5,1),
            ])
        if con.execute("SELECT COUNT(*) FROM stock").fetchone()[0] == 0:
            con.executemany("INSERT INTO stock(name,category,quantity,minimum,expiry) VALUES(?,?,?,?,?)", [
                ("Pão de hambúrguer","Insumos",18,20,"2026-11-02"),
                ("Carne bovina","Carnes",35,10,"2026-10-29"),
                ("Batata","Hortifruti",6,8,"2026-10-27"),
                ("Queijo","Laticínios",12,5,"2026-11-04"),
            ])
        if con.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
            con.executemany("INSERT INTO employees(name,role,phone,shift,hire_date,status) VALUES(?,?,?,?,?,?)", [
                ("Ana Souza","Cozinheira","(86) 99999-1111","Manhã","2025-02-10","Ativo"),
                ("Carlos Lima","Atendente","(86) 98888-2222","Noite","2025-06-15","Ativo"),
            ])
        if con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            now = datetime.now().isoformat(timespec="minutes")
            con.executemany("INSERT INTO orders(customer,items,total,status,prep_minutes,created_at) VALUES(?,?,?,?,?,?)", [
                ("Mesa 04","Hambúrguer da Casa, Batata frita",40.90,"Aguardando",15,now),
                ("Maria","Suco de laranja",8.50,"Em preparo",5,now),
                ("Mesa 02","Hambúrguer da Casa",28.90,"Concluído",15,now),
            ])
            con.execute("INSERT INTO payments(order_id,customer,amount,method,status,created_at) VALUES(?,?,?,?,?,?)",
                        (1,"Mesa 04",40.90,"PIX","Pago",now))

init_db()

class ProductIn(BaseModel):
    name: str
    category: str = "Geral"
    price: float = 0
    description: str = ""
    ingredients: str = ""
    prep_minutes: int = 0
    available: bool = True

class StockIn(BaseModel):
    name: str
    category: str = "Geral"
    quantity: float = 0
    minimum: float = 0
    expiry: str = ""

class EmployeeIn(BaseModel):
    name: str
    role: str = "Atendente"
    phone: str = ""
    shift: str = "Integral"
    hire_date: str = ""
    status: str = "Ativo"

class OrderIn(BaseModel):
    customer: str = "Cliente balcão"
    items: str = "Pedido"
    total: float = 0
    status: str = "Aguardando"
    prep_minutes: int = 15

class PaymentIn(BaseModel):
    order_id: Optional[int] = None
    customer: str = "Cliente balcão"
    amount: float = 0
    method: str = "PIX"
    status: str = "Pago"

def rows(sql, params=()):
    with db() as con:
        return [dict(r) for r in con.execute(sql, params).fetchall()]

def insert(table, fields, values):
    with db() as con:
        cur = con.execute(f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join(['?']*len(values))})", values)
        return cur.lastrowid

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "MenuFlow"}

@app.post("/api/login")
def login(payload: dict):
    # Demo login for classroom prototype; replace with real hashed-password auth before production.
    if payload.get("username") in ("admin", "admin@menuflow.com") and payload.get("password") == "123456":
        return {"ok": True, "user": "Administrador", "role": "admin"}
    if payload.get("username") in ("cliente", "client", "cliente@menuflow.com") and payload.get("password") == "123456":
        return {"ok": True, "user": "Cliente", "role": "client"}
    if payload.get("username") in ("suporte", "support", "suporte@menuflow.com") and payload.get("password") == "123456":
        return {"ok": True, "user": "Suporte MenuFlow", "role": "platform"}
    raise HTTPException(401, "Usuário ou senha inválidos. Use admin / 123456 para demonstração.")

@app.get("/api/client/restaurants")
def client_restaurants():
    return rows("SELECT id,name,address FROM restaurants WHERE status=\'Aprovado\' ORDER BY name")

@app.get("/api/client/products")
def client_products():
    return rows("SELECT id,name,category,price,description,available FROM products WHERE available=1 ORDER BY category,name")

@app.post("/api/client/orders")
def client_create_order(payload: dict):
    customer=str(payload.get("customer", "Cliente" )).strip() or "Cliente"
    items=str(payload.get("items", "")).strip()
    total=float(payload.get("total",0))
    if not items or total <= 0: raise HTTPException(400,"Pedido e valor são obrigatórios")
    now=datetime.now().isoformat(timespec="minutes")
    i=insert("orders",["customer","items","total","status","prep_minutes","created_at"],[customer,items,total,"Aguardando",15,now])
    return rows("SELECT * FROM orders WHERE id=?",(i,))[0]

@app.post("/api/client/register")
def client_register(payload: dict):
    name=str(payload.get("name", "")).strip(); email=str(payload.get("email", "")).strip().lower(); phone=str(payload.get("phone", "")).strip()
    if not name or not email: raise HTTPException(400, "Nome e e-mail são obrigatórios")
    try: i=insert("customer_accounts", ["name","email","phone","created_at"], [name,email,phone,datetime.now().isoformat(timespec="minutes")])
    except sqlite3.IntegrityError: raise HTTPException(409, "Este e-mail já está cadastrado")
    return rows("SELECT id,name,email,phone FROM customer_accounts WHERE id=?",(i,))[0]

@app.get("/api/platform/restaurants")
def platform_restaurants():
    return rows("SELECT * FROM restaurants ORDER BY id DESC")

@app.post("/api/platform/restaurants")
def restaurant_request(payload: dict):
    name=str(payload.get("name", "")).strip(); owner=str(payload.get("owner", "")).strip(); email=str(payload.get("email", "")).strip(); phone=str(payload.get("phone", "")).strip(); address=str(payload.get("address", "")).strip()
    if not name or not owner or not email: raise HTTPException(400,"Estabelecimento, responsável e e-mail são obrigatórios")
    i=insert("restaurants", ["name","owner","email","phone","address","status","created_at"],[name,owner,email,phone,address,"Pendente",datetime.now().isoformat(timespec="minutes")])
    return rows("SELECT * FROM restaurants WHERE id=?",(i,))[0]

@app.patch("/api/platform/restaurants/{restaurant_id}")
def restaurant_status(restaurant_id:int, payload:dict):
    status=str(payload.get("status",""))
    if status not in ("Pendente","Aprovado","Suspenso"): raise HTTPException(400,"Status inválido")
    with db() as con: cur=con.execute("UPDATE restaurants SET status=? WHERE id=?",(status,restaurant_id))
    if cur.rowcount==0: raise HTTPException(404,"Cadastro não encontrado")
    return rows("SELECT * FROM restaurants WHERE id=?",(restaurant_id,))[0]

@app.get("/api/platform/customers")
def platform_customers():
    return rows("SELECT id,name,email,phone,created_at FROM customer_accounts ORDER BY id DESC")

@app.get("/api/dashboard")
def dashboard():
    with db() as con:
        sales = con.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='Pago'").fetchone()[0]
        order_count = con.execute("SELECT COUNT(*) FROM orders WHERE status!='Concluído'").fetchone()[0]
        low_stock = con.execute("SELECT COUNT(*) FROM stock WHERE quantity < minimum").fetchone()[0]
        team = con.execute("SELECT COUNT(*) FROM employees WHERE status='Ativo'").fetchone()[0]
    return {"sales": sales, "open_orders": order_count, "low_stock": low_stock, "active_employees": team}

@app.get("/api/products")
def get_products():
    return rows("SELECT * FROM products ORDER BY id DESC")

@app.post("/api/products")
def create_product(p: ProductIn):
    i = insert("products", ["name","category","price","description","ingredients","prep_minutes","available"],
        [p.name,p.category,p.price,p.description,p.ingredients,p.prep_minutes,int(p.available)])
    return rows("SELECT * FROM products WHERE id=?", (i,))[0]

@app.put("/api/products/{item_id}")
def update_product(item_id: int, p: ProductIn):
    with db() as con:
        cur = con.execute("""UPDATE products SET name=?,category=?,price=?,description=?,ingredients=?,prep_minutes=?,available=? WHERE id=?""",
            [p.name,p.category,p.price,p.description,p.ingredients,p.prep_minutes,int(p.available),item_id])
        if not cur.rowcount: raise HTTPException(404,"Produto não encontrado")
    return rows("SELECT * FROM products WHERE id=?", (item_id,))[0]

@app.delete("/api/products/{item_id}")
def delete_product(item_id: int):
    with db() as con:
        cur = con.execute("DELETE FROM products WHERE id=?", (item_id,))
        if not cur.rowcount: raise HTTPException(404,"Produto não encontrado")
    return {"ok": True}

@app.get("/api/stock")
def get_stock():
    return rows("SELECT *, CASE WHEN quantity < minimum THEN 'Baixo' ELSE 'Normal' END AS status FROM stock ORDER BY id DESC")

@app.post("/api/stock")
def create_stock(s: StockIn):
    i = insert("stock", ["name","category","quantity","minimum","expiry"], [s.name,s.category,s.quantity,s.minimum,s.expiry])
    return rows("SELECT * FROM stock WHERE id=?", (i,))[0]

@app.put("/api/stock/{item_id}")
def update_stock(item_id: int, s: StockIn):
    with db() as con:
        cur = con.execute("UPDATE stock SET name=?,category=?,quantity=?,minimum=?,expiry=? WHERE id=?",
            [s.name,s.category,s.quantity,s.minimum,s.expiry,item_id])
        if not cur.rowcount: raise HTTPException(404,"Item não encontrado")
    return rows("SELECT * FROM stock WHERE id=?", (item_id,))[0]

@app.get("/api/stock/movements")
def get_stock_movements():
    return rows("SELECT m.*, s.name AS item_name FROM stock_movements m JOIN stock s ON s.id=m.stock_id ORDER BY m.id DESC")

@app.post("/api/stock/movements")
def create_stock_movement(payload: dict):
    stock_id=int(payload.get("stock_id",0)); kind=payload.get("kind"); qty=float(payload.get("quantity",0)); note=str(payload.get("note", ""))
    if kind not in ["Entrada","Saída"] or qty <= 0: raise HTTPException(400,"Tipo e quantidade válida são obrigatórios")
    with db() as con:
        item=con.execute("SELECT quantity FROM stock WHERE id=?",(stock_id,)).fetchone()
        if not item: raise HTTPException(404,"Item de estoque não encontrado")
        newqty=item[0]+qty if kind=="Entrada" else item[0]-qty
        if newqty < 0: raise HTTPException(400,"Saída maior que o estoque disponível")
        con.execute("UPDATE stock SET quantity=? WHERE id=?",(newqty,stock_id))
        con.execute("INSERT INTO stock_movements(stock_id,kind,quantity,note,created_at) VALUES(?,?,?,?,?)",(stock_id,kind,qty,note,datetime.now().isoformat(timespec="minutes")))
    return {"ok":True,"quantity":newqty}

@app.get("/api/employees")
def get_employees():
    return rows("SELECT * FROM employees ORDER BY id DESC")

@app.post("/api/employees")
def create_employee(e: EmployeeIn):
    i = insert("employees", ["name","role","phone","shift","hire_date","status"], [e.name,e.role,e.phone,e.shift,e.hire_date,e.status])
    return rows("SELECT * FROM employees WHERE id=?", (i,))[0]

@app.put("/api/employees/{item_id}")
def update_employee(item_id: int, e: EmployeeIn):
    with db() as con:
        cur = con.execute("UPDATE employees SET name=?,role=?,phone=?,shift=?,hire_date=?,status=? WHERE id=?",
            [e.name,e.role,e.phone,e.shift,e.hire_date,e.status,item_id])
        if not cur.rowcount: raise HTTPException(404,"Funcionário não encontrado")
    return rows("SELECT * FROM employees WHERE id=?", (item_id,))[0]

@app.get("/api/orders")
def get_orders():
    return rows("SELECT * FROM orders ORDER BY id DESC")

@app.post("/api/orders")
def create_order(o: OrderIn):
    now = datetime.now().isoformat(timespec="minutes")
    i = insert("orders", ["customer","items","total","status","prep_minutes","created_at"], [o.customer,o.items,o.total,o.status,o.prep_minutes,now])
    return rows("SELECT * FROM orders WHERE id=?", (i,))[0]

@app.patch("/api/orders/{item_id}/status")
def update_order_status(item_id: int, payload: dict):
    status = payload.get("status")
    if status not in ["Aguardando","Em preparo","Concluído"]:
        raise HTTPException(400,"Status inválido")
    with db() as con:
        cur = con.execute("UPDATE orders SET status=? WHERE id=?", (status,item_id))
        if not cur.rowcount: raise HTTPException(404,"Pedido não encontrado")
    return rows("SELECT * FROM orders WHERE id=?", (item_id,))[0]

@app.get("/api/payments")
def get_payments():
    return rows("SELECT * FROM payments ORDER BY id DESC")

@app.post("/api/payments")
def create_payment(p: PaymentIn):
    now = datetime.now().isoformat(timespec="minutes")
    i = insert("payments", ["order_id","customer","amount","method","status","created_at"], [p.order_id,p.customer,p.amount,p.method,p.status,now])
    return rows("SELECT * FROM payments WHERE id=?", (i,))[0]

@app.get("/api/reports")
def reports():
    with db() as con:
        sales = con.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='Pago'").fetchone()[0]
        expenses = con.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0]
        count = con.execute("SELECT COUNT(*) FROM payments WHERE status='Pago'").fetchone()[0]
        by_method = [dict(r) for r in con.execute("SELECT method, SUM(amount) AS total FROM payments WHERE status='Pago' GROUP BY method").fetchall()]
        by_category = [dict(r) for r in con.execute("SELECT category, SUM(price) AS total FROM products GROUP BY category").fetchall()]
    return {"sales":sales,"expenses":expenses,"result":sales-expenses,"payments_count":count,
            "average_ticket": sales/count if count else 0, "by_method":by_method,"by_category":by_category}

@app.post("/api/expenses")
def create_expense(payload: dict):
    description = str(payload.get("description","Despesa"))
    amount = float(payload.get("amount",0))
    i = insert("expenses", ["description","amount","created_at"], [description,amount,datetime.now().isoformat(timespec="minutes")])
    return rows("SELECT * FROM expenses WHERE id=?", (i,))[0]

app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
