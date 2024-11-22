from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, date
import pymysql
from dotenv import load_dotenv
import os
import bcrypt
from typing import List

# .env 파일 경로를 명시적으로 지정
load_dotenv()

print("DB_HOST:", os.getenv("DB_HOST"))
print("DB_USER:", os.getenv("DB_USER"))
print("DB_PASSWORD:", os.getenv("DB_PASSWORD"))
print("DB_NAME:", os.getenv("DB_NAME"))

# FastAPI 앱 생성
app = FastAPI()

# 데이터베이스 연결 설정
def get_db_connection():
    try:
        return pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Pydantic 모델 정의
class LoginRequest(BaseModel):
    email: str
    password: str

class CustomerResponse(BaseModel):
    customer_id: int
    name: str
    email: str
    created_at: datetime

class RiskToleranceResponse(BaseModel):
    risk_tolerance: str

class CustomerFundResponse(BaseModel):
    customer_id: int
    fund_id: int
    investment_percentage: float
    investment_amount: float
    created_at: datetime

class FundPriceResponse(BaseModel):
    fund_id: int
    date: date
    fund_price: float
    benchmark_price: float

class AssetCompositionResponse(BaseModel):
    asset_name: str
    proportion: float

class AssetManagementCompanyResponse(BaseModel):
    name: str


# 비밀번호 검증 함수
def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


@app.get("/")
async def root():
    return {"message": "Welcome to the Fund API"}

# 1. 로그인 API
@app.post("/login", response_model=CustomerResponse)
async def login(login_request: LoginRequest):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            # 이메일로 고객 정보 조회
            cursor.execute(
                """
                SELECT customer_id, name, email, password_hash, created_at
                FROM customers
                WHERE email = %s
                """,
                (login_request.email,)
            )
            customer = cursor.fetchone()

            if not customer:
                raise HTTPException(status_code=404, detail="Invalid email or password")

            # 비밀번호 검증
            if not verify_password(login_request.password, customer["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid email or password")

    # 인증 성공 시 고객 정보 반환
    return CustomerResponse(
        customer_id=customer["customer_id"],
        name=customer["name"],
        email=customer["email"],
        created_at=customer["created_at"]
    )

# 2. 전체 고객 목록 조회 API
@app.get("/customers", response_model=List[CustomerResponse])
async def get_all_customers():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT customer_id, name, email, created_at
                FROM customers
                """
            )
            customers = cursor.fetchall()

    return [CustomerResponse(**customer) for customer in customers]

# 3. 특정 고객 정보 조회 API
@app.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int):
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT customer_id, name, email, created_at
                FROM customers
                WHERE customer_id = %s
                """,
                (customer_id,)
            )
            customer = cursor.fetchone()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return CustomerResponse(**customer)

###########################################################3

# 특정 고객의 리스크 성향 조회 API
@app.get("/customers/{customer_id}/risk-tolerance", response_model=RiskToleranceResponse)
async def get_risk_tolerance(customer_id: int):
    """
    특정 고객의 리스크 성향 조회 API
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT cp.risk_tolerance
                FROM customer_profile cp
                JOIN customers c ON cp.customer_id = c.customer_id
                WHERE c.customer_id = %s
                """,
                (customer_id,)
            )
            result = cursor.fetchone()
    finally:
        connection.close()

    if not result:
        raise HTTPException(status_code=404, detail="Risk tolerance not found for the given customer_id")

    return RiskToleranceResponse(**result)

# 특정 고객의 투자 정보를 조회하는 API
@app.get("/customers/{customer_id}/investments", response_model=List[CustomerFundResponse])
async def get_customer_investments(customer_id: int):
    """
    특정 고객의 투자 정보를 조회하는 API
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT cf.customer_id, cf.fund_id, cf.investment_percentage, cf.investment_amount, cf.created_at
                FROM customer_fund cf
                JOIN fund f ON f.fund_id = cf.fund_id
                WHERE cf.customer_id = %s
                """,
                (customer_id,)
            )
            results = cursor.fetchall()
    finally:
        connection.close()

    if not results:
        raise HTTPException(status_code=404, detail="No investments found for the given customer_id")

    return [CustomerFundResponse(**result) for result in results]




########################################################33

# 펀드 목록 조회 API
@app.get("/funds")
async def get_funds():
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM fund")
        funds = cursor.fetchall()
    connection.close()
    return {"funds": funds}

# 특정 펀드 조회 API
@app.get("/funds/{fund_id}")
async def get_fund(fund_id: int):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM fund WHERE fund_id = %s", (fund_id,))
        fund = cursor.fetchone()
    connection.close()
    if not fund:
        return {"error": "Fund not found"}
    return {"fund": fund}


#########################################################3

# 특정 펀드의 최신 가격 조회 API

@app.get("/funds/{fund_id}/price", response_model=FundPriceResponse)
async def get_latest_fund_price(fund_id: int):
    """
    특정 펀드의 최신 가격 조회
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT fp.fund_id, fp.date, fp.fund_price, fp.benchmark_price
                FROM price_data fp
                LEFT OUTER JOIN fund f ON f.fund_id = fp.fund_id
                WHERE fp.fund_id = %s
                ORDER BY fp.date DESC
                LIMIT 1
                """,
                (fund_id,)
            )
            result = cursor.fetchone()
    finally:
        connection.close()

    if not result:
        raise HTTPException(status_code=404, detail="Fund price not found")

    return FundPriceResponse(**result)


# 특정 펀드의 기간별 가격 조회
@app.get("/funds/{fund_id}/prices", response_model=List[FundPriceResponse])
async def get_fund_prices_by_period(
    fund_id: int,
    start_date: date = Query(..., description="조회 시작 날짜 (YYYY-MM-DD)"),
    end_date: date = Query(..., description="조회 종료 날짜 (YYYY-MM-DD)")
):
    """
    특정 펀드의 기간별 가격 조회
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT fp.fund_id, fp.date, fp.fund_price, fp.benchmark_price
                FROM price_data fp
                LEFT OUTER JOIN fund f ON f.fund_id = fp.fund_id
                WHERE fp.fund_id = %s AND fp.date BETWEEN %s AND %s
                ORDER BY fp.date ASC
                """,
                (fund_id, start_date, end_date)
            )
            results = cursor.fetchall()
    finally:
        connection.close()

    if not results:
        raise HTTPException(status_code=404, detail="No fund prices found for the given period")

    return [FundPriceResponse(**result) for result in results]


# 특정 펀드의 특정 날짜 가격 조회
@app.get("/funds/{fund_id}/price/{specific_date}", response_model=FundPriceResponse)
async def get_fund_price_by_date(fund_id: int, specific_date: date):
    """
    특정 펀드의 특정 날짜 가격 조회
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT fp.fund_id, fp.date, fp.fund_price, fp.benchmark_price
                FROM price_data fp
                LEFT OUTER JOIN fund f ON f.fund_id = fp.fund_id
                WHERE fp.fund_id = %s AND fp.date = %s
                """,
                (fund_id, specific_date)
            )
            result = cursor.fetchone()
    finally:
        connection.close()

    if not result:
        raise HTTPException(status_code=404, detail="Fund price not found for the given date")

    return FundPriceResponse(**result)


##########################################################

# 특정 펀드의 자산 구성 조회 API
@app.get("/funds/{fund_id}/assets", response_model=List[AssetCompositionResponse])
async def get_asset_composition(fund_id: int):
    """
    특정 펀드의 자산 구성 조회 API
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ac.asset_name, ac.proportion
                FROM asset_composition ac
                JOIN fund f ON f.fund_id = ac.fund_id
                WHERE ac.fund_id = %s
                """,
                (fund_id,)
            )
            results = cursor.fetchall()
    finally:
        connection.close()

    if not results:
        raise HTTPException(status_code=404, detail="No asset composition found for the given fund_id")

    return [AssetCompositionResponse(**result) for result in results]

###########################################################

@app.get("/funds/{fund_id}/asset-management-company", response_model=AssetManagementCompanyResponse)
async def get_asset_management_company(fund_id: int):
    """
    특정 펀드의 자산운용사 이름 조회 API
    """
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT amc.name
                FROM asset_management_company amc
                JOIN fund f ON amc.asset_management_company_id = f.asset_management_company_id
                WHERE f.fund_id = %s
                """,
                (fund_id,)
            )
            result = cursor.fetchone()
    finally:
        connection.close()

    if not result:
        raise HTTPException(status_code=404, detail="Asset management company not found for the given fund_id")

    return AssetManagementCompanyResponse(**result)








