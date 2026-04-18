from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routers import regions, triage, funding, counterfactual, news, charities, fund

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application startup and teardown
@app.on_event("startup")
async def startup_event():
    print("Initializing THRESHOLD backend models & cache...")
    # Load ML models and establish DB connection to Snowflake here

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "THRESHOLD Systems Nominal"}

# Register routers
app.include_router(regions.router, prefix=settings.API_V1_STR + "/regions", tags=["regions"])
app.include_router(triage.router, prefix=settings.API_V1_STR + "/triage", tags=["triage"])
app.include_router(funding.router, prefix=settings.API_V1_STR + "/funding", tags=["funding"])
app.include_router(news.router, prefix=settings.API_V1_STR + "/news", tags=["news"])
app.include_router(counterfactual.router, prefix=settings.API_V1_STR + "/counterfactual", tags=["counterfactual"])
app.include_router(charities.router, prefix=settings.API_V1_STR + "/charities", tags=["charities"])
app.include_router(fund.router, prefix=settings.API_V1_STR + "/fund", tags=["fund"])
