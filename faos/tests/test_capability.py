import pytest
from faos.services.capability.models import CapabilityManifest
from faos.services.capability.service import CapabilityService

def test_capability_service_registration():
    service = CapabilityService()
    
    manifest = CapabilityManifest(
        id="cap.test.1",
        name="TestCapability",
        inputs=["param1"],
        outputs=["result1"]
    )
    
    service.register_capability(manifest)
    
    retrieved = service.get_capability("TestCapability")
    assert retrieved is not None
    assert retrieved.id == "cap.test.1"
    assert "param1" in retrieved.inputs
    
    not_found = service.get_capability("NonExistent")
    assert not_found is None
