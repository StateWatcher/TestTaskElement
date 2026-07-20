from fastapi import APIRouter

from app.transports.rest.routers import auth, bookings, lots, requests, sets

router = APIRouter()
router.include_router(auth.router)
router.include_router(lots.router)
router.include_router(bookings.router)
router.include_router(requests.router)
router.include_router(sets.router)
