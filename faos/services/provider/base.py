from abc import ABC, abstractmethod
from faos.services.provider.models import ProviderRequest, ProviderResponse, ProviderManifest

class BaseProvider(ABC):
    """
    Abstract base class for all Data Providers in FAOS.
    Providers are the unified data access layer.
    """
    
    @property
    @abstractmethod
    def manifest(self) -> ProviderManifest:
        """Return the manifest describing this provider."""
        pass
        
    @abstractmethod
    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        """
        Fetch data from the external source and convert to standard model.
        """
        pass
