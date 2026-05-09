from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, users, orders, contracts, disputes, notifications, admin

app = FastAPI(
    title="OpenDealz API",
    description="Freelance marketplace with programmatic smart contracts",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(orders.router)
app.include_router(contracts.router)
app.include_router(disputes.router)
app.include_router(notifications.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
