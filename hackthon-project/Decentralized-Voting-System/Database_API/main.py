# main.py
import os
import dotenv
from fastapi import FastAPI, HTTPException, status, Request, Depends, Form
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from mysql.connector import connect, Error
import jwt
from jwt import PyJWTError
from datetime import datetime, timedelta

# Load environment variables
dotenv.load_dotenv()

# Initialize FastAPI
app = FastAPI()

# CORS setup
origins = ["http://localhost:8080", "http://127.0.0.1:8080"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
try:
    cnx = connect(
        user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'],
        host=os.environ['MYSQL_HOST'],
        database=os.environ['MYSQL_DB']
    )
    cursor = cnx.cursor(dictionary=True)
except Error as err:
    print("Database connection error:", err)
    raise

# Secret key for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # token valid for 1 hour


# Utility to create JWT token
def create_jwt_token(voter_id: str, role: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "voter_id": voter_id,
        "role": role,
        "exp": expire
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


# Utility to verify JWT token
def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        voter_id: str = payload.get("voter_id")
        role: str = payload.get("role")
        if voter_id is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authorization token")


# Dependency to use in protected routes
async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = auth_header.replace("Bearer ", "")
    return verify_jwt_token(token)


class AddCandidatePayload(BaseModel):
    name: str
    party: str


class SetDatesPayload(BaseModel):
    startDate: str
    endDate: str


# Login endpoint

# Login endpoint - remove role checking
@app.post("/login")
async def login(voter_id: str = Form(...), password: str = Form(...)):
    try:
        cursor.execute(
            "SELECT role FROM voters WHERE voter_id=%s AND password=%s",
            (voter_id, password)
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid voter ID or password")

        db_role = user["role"]
        token = create_jwt_token(voter_id, db_role)
        return {"success": True, "token": token, "role": db_role}
    except Error as err:
        print("DB error:", err)
        raise HTTPException(status_code=500, detail="Database error")


# Example protected route
@app.get("/profile")
async def profile(user: dict = Depends(get_current_user)):
    # user contains decoded token data
    return {"message": f"Hello {user['voter_id']}, your role is {user['role']}"}


# Admin-only: add candidate
@app.post("/add-candidate")
async def add_candidate(payload: AddCandidatePayload, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    # TODO: persist candidate to DB/blockchain if applicable
    return {"success": True, "message": "Candidate added", "data": payload.dict()}


# Admin-only: set voting dates
@app.post("/set-dates")
async def set_dates(payload: SetDatesPayload, user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    # TODO: persist dates
    return {"success": True, "message": "Voting dates set", "data": payload.dict()}


# Run the app using: uvicorn main:app --reload
