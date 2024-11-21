from cerebrum.client import Cerebrum

class Config:
   def __init__(self):
       self._global_client: Cerebrum = None
       self._base_url = "http://localhost:8000"
       self._timeout = 30
   
   @property
   def global_client(self):
       if not self._global_client:
           raise ValueError("Client not set. Call config.client = Cerebrum Client")
       return self._global_client
       
   @global_client.setter 
   def global_client(self, value):
       self._global_client = value

   def configure(self, **kwargs):
       """Configure multiple settings at once"""
       for key, value in kwargs.items():
           if hasattr(self, f"_{key}"):
               setattr(self, f"_{key}", value)

config = Config()
