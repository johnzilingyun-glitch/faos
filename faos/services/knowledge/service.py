from typing import List, Optional
import logging
from faos.services.knowledge.models import KnowledgeItem, KnowledgePackage, KnowledgeCategory
from faos.services.knowledge.registry import KnowledgeRegistry

logger = logging.getLogger(__name__)

class KnowledgeService:
    """
    Knowledge Service is the central hub for static knowledge in FAOS.
    It manages financial knowledge, industry knowledge, prompts, and capability knowledge.
    """
    def __init__(self):
        self.registry = KnowledgeRegistry()
        logger.info("KnowledgeService initialized")

    def register_item(self, item: KnowledgeItem):
        """Registers a single KnowledgeItem."""
        self.registry.register_item(item)

    def register_package(self, package: KnowledgePackage):
        """Registers a KnowledgePackage."""
        self.registry.register_package(package)

    def get_knowledge_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """Retrieve a specific knowledge item by its ID."""
        return self.registry.get_item(item_id)

    def load_knowledge_package(self, package_id: str) -> List[KnowledgeItem]:
        """
        Dynamically loads and resolves all items within a KnowledgePackage.
        Returns a list of resolved KnowledgeItems.
        """
        logger.info(f"Loading Knowledge Package: {package_id}")
        return self.registry.resolve_package_items(package_id)

    def get_knowledge_by_category(self, category: KnowledgeCategory) -> List[KnowledgeItem]:
        """Retrieve all registered knowledge items for a given category."""
        return self.registry.get_items_by_category(category)

    def get_all_capabilities(self) -> List[KnowledgeItem]:
        """
        Retrieves all registered capability knowledge items.
        Useful for the Planner to understand what the system is capable of.
        """
        return self.get_knowledge_by_category(KnowledgeCategory.CAPABILITY)
