"""
Memory Service - Gestion de la mémoire de session pour SolarXBot v5.1
=====================================================================
"""

import os
import json
import uuid
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import threading

# Configuration
MEMORY_CACHE_PATH = os.environ.get("MEMORY_CACHE_PATH", "/app/cache/memory_sessions.json")
MAX_HISTORY_LENGTH = 50
SESSION_TIMEOUT_HOURS = 24


@dataclass
class ChatMessage:
    """Un message"""
    role: str
    text: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class ChatSession:
    """Une session de chat"""
    session_id: str
    title: str = "Nouvelle conversation"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    messages: List[Dict] = field(default_factory=list)
    summary: str = ""
    topics: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatSession':
        return cls(**data)


@dataclass
class ConversationContext:
    """Contexte de conversation"""
    communes_mentioned: List[str] = field(default_factory=list)
    zones_mentioned: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)


class MemoryService:
    """Service de gestion de la mémoire"""
    
    def __init__(self):
        self._sessions: Dict[str, ChatSession] = {}
        self._contexts: Dict[str, ConversationContext] = {}
        self._lock = threading.Lock()
        self._load_sessions()
    
    def _load_sessions(self):
        """Charge les sessions depuis le cache"""
        if not os.path.exists(MEMORY_CACHE_PATH):
            return
        
        try:
            with open(MEMORY_CACHE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for session_id, session_data in data.items():
                    self._sessions[session_id] = ChatSession.from_dict(session_data)
        except Exception as e:
            print(f"Erreur chargement sessions: {e}")
    
    def _save_sessions(self):
        """Sauvegarde les sessions"""
        try:
            os.makedirs(os.path.dirname(MEMORY_CACHE_PATH), exist_ok=True)
            with open(MEMORY_CACHE_PATH, 'w', encoding='utf-8') as f:
                data = {sid: s.to_dict() for sid, s in self._sessions.items()}
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur sauvegarde sessions: {e}")
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Crée une nouvelle session"""
        with self._lock:
            session_id = str(uuid.uuid4())[:16]
            self._sessions[session_id] = ChatSession(session_id=session_id)
            self._contexts[session_id] = ConversationContext()
            self._save_sessions()
            return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Récupère une session"""
        return self._sessions.get(session_id)
    
    def add_message(self, session_id: str, role: str, text: str, 
                   metadata: Optional[Dict] = None) -> bool:
        """Ajoute un message"""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            message = ChatMessage(
                role=role,
                text=text,
                metadata=metadata or {}
            )
            
            session.messages.append(asdict(message))
            session.updated_at = datetime.now().isoformat()
            
            # Extraire contexte
            self._extract_context(session_id, text)
            
            # Générer titre si premier message user
            if role == "user" and len([m for m in session.messages if m["role"] == "user"]) == 1:
                session.title = self._generate_title(text)
            
            # Limiter taille
            if len(session.messages) > MAX_HISTORY_LENGTH:
                session.messages = session.messages[-MAX_HISTORY_LENGTH//2:]
            
            self._save_sessions()
            return True
    
    def _extract_context(self, session_id: str, text: str):
        """Extrait le contexte"""
        if session_id not in self._contexts:
            self._contexts[session_id] = ConversationContext()
        
        ctx = self._contexts[session_id]
        text_lower = text.lower()
        
        # Communes
        communes = ["genève", "meyrin", "vernier", "carouge", "lancy", "thonex", "onex"]
        for commune in communes:
            if commune in text_lower and commune not in ctx.communes_mentioned:
                ctx.communes_mentioned.append(commune)
        
        # Zones
        zones = ["ziplo", "cern", "pav"]
        for zone in zones:
            if zone in text_lower and zone not in ctx.zones_mentioned:
                ctx.zones_mentioned.append(zone)
        
        # Topics
        topic_keywords = {
            "production": ["production", "kwh", "énergie"],
            "température": ["température", "chaleur"],
            "ensoleillement": ["ensoleillement", "soleil"],
            "optimisation": ["optimal", "meilleur"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords) and topic not in ctx.topics:
                ctx.topics.append(topic)
    
    def _generate_title(self, first_message: str) -> str:
        """Génère un titre"""
        if len(first_message) <= 50:
            return first_message
        
        # Chercher communes
        communes = ["genève", "meyrin", "vernier", "carouge"]
        keywords = []
        
        msg_lower = first_message.lower()
        for commune in communes:
            if commune in msg_lower:
                keywords.append(commune.title())
                break
        
        # Chercher sujet
        if "production" in msg_lower:
            keywords.append("Production")
        elif "température" in msg_lower:
            keywords.append("Température")
        elif "optimal" in msg_lower:
            keywords.append("Optimisation")
        else:
            keywords.append("Solaire")
        
        return " - ".join(keywords) if keywords else first_message[:40] + "..."
    
    def get_history(self, session_id: str, max_messages: int = 20) -> List[Dict[str, str]]:
        """Récupère l'historique"""
        session = self._sessions.get(session_id)
        if not session:
            return []
        
        history = []
        for msg in session.messages[-max_messages:]:
            history.append({
                "role": msg["role"],
                "text": msg["text"]
            })
        
        return history
    
    def get_context(self, session_id: str) -> ConversationContext:
        """Récupère le contexte"""
        return self._contexts.get(session_id, ConversationContext())
    
    def get_context_summary(self, session_id: str) -> str:
        """Résumé du contexte pour le prompt"""
        ctx = self._contexts.get(session_id)
        if not ctx:
            return ""
        
        parts = []
        if ctx.communes_mentioned:
            parts.append(f"Communes discutées: {', '.join(ctx.communes_mentioned)}")
        if ctx.zones_mentioned:
            parts.append(f"Zones mentionnées: {', '.join(ctx.zones_mentioned)}")
        if ctx.topics:
            parts.append(f"Sujets: {', '.join(ctx.topics)}")
        
        if not parts:
            return ""
        
        return "CONTEXTE CONVERSATION:\n" + "\n".join(parts)
    
    def get_all_sessions(self, limit: int = 20) -> List[Dict]:
        """Liste des sessions récentes"""
        sessions = list(self._sessions.values())
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        
        return [
            {
                "session_id": s.session_id,
                "title": s.title,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": len(s.messages),
                "topics": self._contexts.get(s.session_id, ConversationContext()).topics[:3]
            }
            for s in sessions[:limit]
        ]
    
    def delete_session(self, session_id: str) -> bool:
        """Supprime une session"""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                if session_id in self._contexts:
                    del self._contexts[session_id]
                self._save_sessions()
                return True
            return False


# Singleton
_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
