import pickle
from datetime import timedelta

import redis

from core.endeavor import Endeavor


class SessionManager:
    def __init__(self, host: str, port: int, db: int, ttl_hours: int):
        self.r = redis.Redis(host=host, port=port, db=db)
        self.ttl = timedelta(hours=ttl_hours)

    def save_endeavor(self, session_id: str, endeavor_obj: Endeavor):
        serialized_endeavor = pickle.dumps(endeavor_obj)
        self.r.setex(f"{session_id}", self.ttl, serialized_endeavor)

    def refresh_endeavor_ttl(self, session_id: str, hours: int):
        self.r.expire(f"{session_id}", timedelta(hours=hours))

    def update_endeavor(self, session_id: str, endeavor_obj: Endeavor, hours: int):
        serialized_endeavor = pickle.dumps(endeavor_obj)
        self.r.set(f"{session_id}", serialized_endeavor)
        self.refresh_endeavor_ttl(session_id, hours)

    def load_endeavor(self, session_id: str):
        data = self.r.get(f"{session_id}")
        if data:
            return pickle.loads(data)
        return None