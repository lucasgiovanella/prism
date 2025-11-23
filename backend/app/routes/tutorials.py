from fastapi import APIRouter, Request, HTTPException
import database

router = APIRouter()

@router.post("/tutorials")
async def create_tutorial_endpoint(request: Request):
    """Create a new tutorial."""
    data = await request.json()
    title = data.get('title', 'Untitled Tutorial')
    steps = data.get('steps', [])
    
    tutorial_id = database.create_tutorial(title, steps)
    return {"id": tutorial_id, "message": "Tutorial created successfully"}

@router.get("/tutorials")
async def get_tutorials():
    """Get recent tutorials."""
    tutorials = database.get_recent_tutorials(limit=10)
    return {"tutorials": tutorials}

@router.get("/tutorials/{tutorial_id}")
async def get_tutorial_endpoint(tutorial_id: str):
    """Get a specific tutorial."""
    tutorial = database.get_tutorial(tutorial_id)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    return tutorial

@router.put("/tutorials/{tutorial_id}")
async def update_tutorial_endpoint(tutorial_id: str, request: Request):
    """Update an existing tutorial."""
    data = await request.json()
    title = data.get('title', 'Untitled Tutorial')
    steps = data.get('steps', [])
    
    success = database.update_tutorial(tutorial_id, title, steps)
    if success:
        return {"message": "Tutorial updated successfully"}
    raise HTTPException(status_code=500, detail="Failed to update tutorial")

@router.delete("/tutorials/{tutorial_id}")
async def delete_tutorial_endpoint(tutorial_id: str):
    """Delete a tutorial."""
    success = database.delete_tutorial(tutorial_id)
    if success:
        return {"message": "Tutorial deleted successfully"}
    raise HTTPException(status_code=500, detail="Failed to delete tutorial")
