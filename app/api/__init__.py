from fastapi import APIRouter

from . import auth, courses, users, course_templates, participants, venues

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(course_templates.router, prefix="/course-templates", tags=["course-templates"])
api_router.include_router(participants.router, prefix="/participants", tags=["participants"])
api_router.include_router(venues.router, prefix="/venues", tags=["venues"])


