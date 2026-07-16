from typing import Dict, List, Optional
import logging
from faos.services.knowledge.models import KnowledgeItem, KnowledgePackage, KnowledgeCategory

logger = logging.getLogger(__name__)

class KnowledgeRegistry:
    """
    Central registry for managing static knowledge in FAOS.
    Tracks all KnowledgeItems and KnowledgePackages.
    """
    def __init__(self):
        self._items: Dict[str, KnowledgeItem] = {}
        self._packages: Dict[str, KnowledgePackage] = {}

    def register_item(self, item: KnowledgeItem):
        """Registers a single KnowledgeItem."""
        if item.id in self._items:
            logger.warning(f"KnowledgeItem {item.id} is being overwritten.")
        self._items[item.id] = item
        logger.debug(f"Registered KnowledgeItem: {item.id} ({item.category})")

    def register_package(self, package: KnowledgePackage):
        """Registers a KnowledgePackage."""
        if package.id in self._packages:
            logger.warning(f"KnowledgePackage {package.id} is being overwritten.")
        self._packages[package.id] = package
        logger.info(f"Registered KnowledgePackage: {package.id}")

    def get_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """Retrieve a specific KnowledgeItem by ID."""
        return self._items.get(item_id)

    def get_package(self, package_id: str) -> Optional[KnowledgePackage]:
        """Retrieve a specific KnowledgePackage by ID."""
        return self._packages.get(package_id)

    def get_items_by_category(self, category: KnowledgeCategory) -> List[KnowledgeItem]:
        """Retrieve all KnowledgeItems belonging to a specific category."""
        return [item for item in self._items.values() if item.category == category]

    def resolve_package_items(self, package_id: str) -> List[KnowledgeItem]:
        """
        Resolves a package into a list of its included KnowledgeItems.
        Returns an empty list if package is not found.
        """
        package = self.get_package(package_id)
        if not package:
            logger.warning(f"KnowledgePackage {package_id} not found.")
            return []
            
        resolved_items = []
        for item_id in package.includes:
            item = self.get_item(item_id)
            if item:
                resolved_items.append(item)
            else:
                logger.warning(f"KnowledgeItem {item_id} referenced in package {package_id} not found.")
                
        return resolved_items
