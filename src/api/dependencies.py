from typing import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


# Django analogy: this is like get_queryset() but explicit and injected per-route
# via Depends(get_db). FastAPI calls it automatically and passes the session in.
async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session
