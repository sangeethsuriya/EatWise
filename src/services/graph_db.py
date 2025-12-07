
from sqlalchemy.orm import Session
from src.db.models import GraphNode, GraphEdge

class GraphService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_graph(self, user_id: int):
        nodes = self.db.query(GraphNode).filter(GraphNode.user_id == user_id).all()
        # Find edges where both source and target belong to this user's nodes
        node_ids = [n.id for n in nodes]
        edges = self.db.query(GraphEdge).filter(
            GraphEdge.source_id.in_(node_ids),
            GraphEdge.target_id.in_(node_ids)
        ).all()
        
        return {
            "nodes": [{"id": n.id, "label": n.label, "type": n.type, "group": n.type} for n in nodes],
            "edges": [{"from": e.source_id, "to": e.target_id, "label": e.relationship} for e in edges]
        }

    def add_node(self, user_id: int, label: str, type: str = "FACT"):
        # Check existing
        existing = self.db.query(GraphNode).filter(
            GraphNode.user_id == user_id, 
            GraphNode.label == label
        ).first()
        if existing:
            return existing
            
        new_node = GraphNode(user_id=user_id, label=label, type=type)
        self.db.add(new_node)
        self.db.commit()
        self.db.refresh(new_node)
        return new_node

    def add_edge(self, source_id: int, target_id: int, relationship: str):
        existing = self.db.query(GraphEdge).filter(
            GraphEdge.source_id == source_id,
            GraphEdge.target_id == target_id,
            GraphEdge.relationship == relationship
        ).first()
        if existing: return existing
        
        edge = GraphEdge(source_id=source_id, target_id=target_id, relationship=relationship)
        self.db.add(edge)
        self.db.commit()
        return edge

    def auto_extract_facts(self, user_id: int, text: str):
        pass

    def delete_node(self, node_id: int):
        # Edges will cascade if configured in DB, else manual delete
        # For SQLite default, let's manual delete edges first
        self.db.query(GraphEdge).filter(
            (GraphEdge.source_id == node_id) | (GraphEdge.target_id == node_id)
        ).delete()
        
        node = self.db.query(GraphNode).filter(GraphNode.id == node_id).first()
        if node:
            self.db.delete(node)
            self.db.commit()
            return True
        return False

    def update_node(self, node_id: int, new_label: str):
        node = self.db.query(GraphNode).filter(GraphNode.id == node_id).first()
        if node:
            node.label = new_label
            self.db.commit()
            return node
        return None
