
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from src.db.database import get_db
from src.db.models import User
from src.services.graph_db import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])

class NodeCreate(BaseModel):
    label: str
    type: str = "FACT"

class NodeUpdate(BaseModel):
    label: str

class EdgeCreate(BaseModel):
    from_id: int
    to_id: int
    relationship: str

@router.get("/")
async def get_graph(user_id: int = 1, db: Session = Depends(get_db)):
    svc = GraphService(db)
    return svc.get_user_graph(user_id)

@router.post("/node")
async def create_node(node: NodeCreate, user_id: int = 1, db: Session = Depends(get_db)):
    svc = GraphService(db)
    new_node = svc.add_node(user_id, node.label, node.type)
    return {"id": new_node.id, "label": new_node.label}

@router.put("/node/{node_id}")
async def update_node(node_id: int, node: NodeUpdate, db: Session = Depends(get_db)):
    svc = GraphService(db)
    updated = svc.update_node(node_id, node.label)
    if not updated:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"status": "updated", "node": {"id": updated.id, "label": updated.label}}

@router.delete("/node/{node_id}")
async def delete_node(node_id: int, db: Session = Depends(get_db)):
    svc = GraphService(db)
    success = svc.delete_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"status": "deleted"}

@router.post("/edge")
async def create_edge(edge: EdgeCreate, db: Session = Depends(get_db)):
    svc = GraphService(db)
    created = svc.add_edge(edge.from_id, edge.to_id, edge.relationship)
    return {"status": "ok"}
