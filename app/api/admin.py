"""
Admin and utility API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models import QuestionLink
from app.services import get_session

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/links")
async def list_links(session: Session = Depends(get_session)):
    """
    List all question links (for debugging/admin purposes).

    Args:
        session: Database session

    Returns:
        List of QuestionLink objects
    """
    statement = select(QuestionLink)
    results = session.exec(statement).all()
    return results


@router.delete("/links/{link_id}")
async def delete_link(
    link_id: int,
    session: Session = Depends(get_session)
):
    """
    Delete a question link (for admin purposes).

    Args:
        link_id: ID of link to delete
        session: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If link not found
    """
    link = session.get(QuestionLink, link_id)

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    session.delete(link)
    session.commit()

    return {"message": f"Link {link_id} deleted successfully"}
