import requests
from src.utils.HttpManager import get_session

class AdminClient:
    API_BASE = "https://mapi.clash.ink/api/admin"
    KEY = "mcf-admin-8888" # Default placeholder, should be configurable
    
    @staticmethod
    def set_key(key):
        AdminClient.KEY = key
        
    @staticmethod
    def get_headers():
        return {"X-Admin-Key": AdminClient.KEY}

    @staticmethod
    def get_blacklist():
        resp = get_session().get(f"{AdminClient.API_BASE}/blacklist", headers=AdminClient.get_headers())
        resp.raise_for_status()
        return resp.json().get("rules", [])
        
    @staticmethod
    def add_blacklist(rule, reason):
        data = {"rule": rule, "reason": reason}
        resp = get_session().post(f"{AdminClient.API_BASE}/blacklist", json=data, headers=AdminClient.get_headers())
        resp.raise_for_status()
        return resp.json()
    
    @staticmethod
    def remove_blacklist(rule):
        data = {"rule": rule}
        resp = get_session().delete(f"{AdminClient.API_BASE}/blacklist", json=data, headers=AdminClient.get_headers())
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_whitelist():
        resp = get_session().get(f"{AdminClient.API_BASE}/whitelist", headers=AdminClient.get_headers())
        resp.raise_for_status()
        return resp.json().get("rules", [])
        
    @staticmethod
    def add_whitelist(rule, description, duration=0):
        data = {"rule": rule, "description": description, "duration_minutes": duration}
        resp = get_session().post(f"{AdminClient.API_BASE}/whitelist", json=data, headers=AdminClient.get_headers())
        resp.raise_for_status()
        return resp.json()
    
    @staticmethod
    def remove_whitelist(rule):
        data = {"rule": rule}
        resp = get_session().delete(f"{AdminClient.API_BASE}/whitelist", json=data, headers=AdminClient.get_headers())
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_access_logs():
        resp = get_session().get(f"{AdminClient.API_BASE}/access_logs", headers=AdminClient.get_headers())
        resp.raise_for_status()
        return resp.json().get("logs", [])

    @staticmethod
    def get_online_users():
        resp = get_session().get(f"{AdminClient.API_BASE}/online_users", headers=AdminClient.get_headers())
        resp.raise_for_status()
        return resp.json().get("users", [])
