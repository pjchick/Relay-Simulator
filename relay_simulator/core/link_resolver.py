"""
Link Resolution System for Relay Logic Simulator

This module implements the link resolution algorithm that connects VNETs across pages
using component link names. The algorithm:

1. Scans all components for LinkName property
2. Builds a map of link names to components
3. Finds VNETs containing tabs from linked components
4. Adds link names to those VNETs for cross-page connectivity
5. Validates link names and detects issues

Link names enable cross-page connections by allowing VNETs on different pages
to be electrically connected without physical wires.
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
from core.vnet import VNET
from core.document import Document


class LinkResolutionResult:
    """
    Result of link resolution process.
    
    Contains statistics and validation information about the link resolution.
    """
    
    def __init__(self):
        self.total_links = 0
        self.resolved_links = 0
        self.unresolved_links: List[str] = []
        self.vnets_with_links = 0
        self.cross_page_links = 0
        self.same_page_links = 0
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
    
    def __repr__(self):
        return (f"LinkResolutionResult(total_links={self.total_links}, "
                f"resolved={self.resolved_links}, "
                f"unresolved={len(self.unresolved_links)}, "
                f"vnets_with_links={self.vnets_with_links}, "
                f"cross_page={self.cross_page_links}, "
                f"warnings={len(self.warnings)}, "
                f"errors={len(self.errors)})")


class LinkResolver:
    """
    Resolves link names to connect VNETs across pages.
    
    The link resolver:
    1. Scans all components for link names
    2. Groups components by link name
    3. Finds VNETs containing tabs from linked components
    4. Adds link names to those VNETs
    5. Validates that links are properly configured
    
    This enables cross-page electrical connections without physical wires.
    """
    
    def resolve_links(
        self,
        document: Document,
        vnets: List[VNET]
    ) -> LinkResolutionResult:
        """
        Resolve all link names in the document.
        
        This is the main entry point for link resolution. It:
        1. Collects all components with link names
        2. Maps link names to component/tab information
        3. Finds VNETs containing linked tabs
        4. Adds link names to those VNETs
        5. Validates link configuration
        
        Args:
            document: Document containing components
            vnets: List of all VNETs (from all pages)
            
        Returns:
            LinkResolutionResult with statistics and validation info
        """
        result = LinkResolutionResult()
        
        # Step 1: Build link name → components map
        link_map = self._build_link_map(document)
        result.total_links = len(link_map)
        
        if result.total_links == 0:
            return result  # No links to resolve
        
        # Step 2: For each link name, find all VNETs containing linked component tabs
        link_to_vnets = self._map_links_to_vnets(link_map, vnets)
        
        # Step 3: Add link names to VNETs
        self._add_links_to_vnets(link_map, link_to_vnets, result)
        
        # Step 4: Validate links
        self._validate_links(link_map, link_to_vnets, result)
        
        return result
    
    def _build_link_map(self, document: Document) -> Dict[str, List[Tuple[str, str, List[str]]]]:
        """
        Build a map of link names to component information.
        
        Includes components from:
        - Main pages
        - Sub-circuit instance pages
        
        Args:
            document: Document to scan for link names
            
        Returns:
            Dict mapping link_name -> list of (component_id, page_id, [tab_ids])
        """
        link_map: Dict[str, List[Tuple[str, str, List[str]]]] = defaultdict(list)
        
        # Scan all components in all pages (including instance pages)
        for page in document.get_all_pages():
            for component in page.get_all_components():
                # Support components that provide per-pin link mappings.
                # Example: BUS returns {'Bus_0': ['comp.pin0.tab'], 'Bus_1': [...], ...}
                get_link_mappings = getattr(component, 'get_link_mappings', None)
                if callable(get_link_mappings):
                    try:
                        mappings = get_link_mappings()
                    except Exception:
                        mappings = None

                    if isinstance(mappings, dict):
                        for link_name, tab_ids in mappings.items():
                            if isinstance(link_name, str):
                                link_name = link_name.strip()
                            else:
                                continue

                            if not link_name:
                                continue

                            if isinstance(tab_ids, (tuple, set)):
                                tab_ids = list(tab_ids)

                            if not isinstance(tab_ids, list):
                                continue

                            cleaned_tab_ids: List[str] = []
                            for tab_id in tab_ids:
                                if isinstance(tab_id, str):
                                    tab_id = tab_id.strip()
                                if tab_id:
                                    cleaned_tab_ids.append(tab_id)

                            if cleaned_tab_ids:
                                link_map[link_name].append((component.component_id, page.page_id, cleaned_tab_ids))

                # Check if component has a link name
                link_name = getattr(component, 'link_name', None)
                if isinstance(link_name, str):
                    link_name = link_name.strip()
                if link_name:
                    
                    # Collect all tab IDs from this component
                    tab_ids = []
                    for pin in component.get_all_pins().values():
                        for tab in pin.tabs.values():
                            tab_ids.append(tab.tab_id)
                    
                    # Add to link map
                    link_map[link_name].append((component.component_id, page.page_id, tab_ids))
        
        return link_map
    
    def _map_links_to_vnets(
        self,
        link_map: Dict[str, List[Tuple[str, str, List[str]]]],
        vnets: List[VNET]
    ) -> Dict[str, Set[VNET]]:
        """
        Map link names to VNETs containing linked component tabs.
        
        For each link name, finds all VNETs that contain tabs from
        components with that link name.
        
        Args:
            link_map: Map of link_name -> component info
            vnets: List of all VNETs
            
        Returns:
            Dict mapping link_name -> set of VNETs
        """
        link_to_vnets: Dict[str, Set[VNET]] = defaultdict(set)
        
        # For each link name
        for link_name, component_infos in link_map.items():
            # Collect all tab IDs for this link
            all_linked_tabs = set()
            for comp_id, page_id, tab_ids in component_infos:
                all_linked_tabs.update(tab_ids)
            
            # Find VNETs containing any of these tabs
            for vnet in vnets:
                for tab_id in all_linked_tabs:
                    if vnet.has_tab(tab_id):
                        link_to_vnets[link_name].add(vnet)
                        break  # Found this VNET, move to next
        
        return link_to_vnets
    
    def _add_links_to_vnets(
        self,
        link_map: Dict[str, List[Tuple[str, str, List[str]]]],
        link_to_vnets: Dict[str, Set[VNET]],
        result: LinkResolutionResult
    ):
        """
        Add link names to VNETs.
        
        Args:
            link_map: Map of link_name -> component info (to check all links)
            link_to_vnets: Map of link_name -> VNETs
            result: Result object to update with statistics
        """
        vnets_updated = set()
        
        # Check all links from link_map (not just those in link_to_vnets)
        for link_name in link_map.keys():
            vnet_set = link_to_vnets.get(link_name, set())
            
            if len(vnet_set) > 0:
                result.resolved_links += 1
                
                # Count cross-page vs same-page links
                page_ids = set(vnet.page_id for vnet in vnet_set if vnet.page_id)
                if len(page_ids) > 1:
                    result.cross_page_links += 1
                else:
                    result.same_page_links += 1
                
                # Add link name to each VNET
                for vnet in vnet_set:
                    vnet.add_link(link_name)
                    vnets_updated.add(vnet)
            else:
                result.unresolved_links.append(link_name)
        
        result.vnets_with_links = len(vnets_updated)
    
    def _validate_links(
        self,
        link_map: Dict[str, List[Tuple[str, str, List[str]]]],
        link_to_vnets: Dict[str, Set[VNET]],
        result: LinkResolutionResult
    ):
        """
        Validate link configuration and add warnings/errors.
        
        Checks:
        - Links with no components
        - Links with only one component (may be intentional)
        - Links that couldn't be resolved to VNETs
        
        Args:
            link_map: Map of link_name -> component info
            link_to_vnets: Map of link_name -> VNETs
            result: Result object to update with warnings/errors
        """
        # Check for unresolved links
        for link_name in result.unresolved_links:
            component_count = len(link_map.get(link_name, []))
            result.add_error(
                f"Link '{link_name}' has {component_count} component(s) but no VNETs found. "
                f"Components may have no tabs or tabs not in any VNET."
            )
        
        # Check for single-component links (warning, not error)
        for link_name, component_infos in link_map.items():
            if len(component_infos) == 1:
                result.add_warning(
                    f"Link '{link_name}' has only one component. "
                    f"Links typically connect multiple components across pages."
                )
        
        # Check for links with no VNETs found
        for link_name, vnet_set in link_to_vnets.items():
            if len(vnet_set) == 0 and link_name not in result.unresolved_links:
                result.unresolved_links.append(link_name)


class LinkValidator:
    """
    Validates link configuration in a document.
    
    Provides utilities to check link names and detect issues
    without modifying VNETs.
    """
    
    @staticmethod
    def find_duplicate_link_names_on_component(document: Document) -> List[Tuple[str, List[str]]]:
        """
        Find components that have duplicate link names (shouldn't happen).
        
        Args:
            document: Document to check
            
        Returns:
            List of (link_name, [component_ids]) for duplicates
        """
        # This would be for detecting if multiple components on same page
        # have conflicting link names (which is actually valid for linking)
        # Not really a duplicate - multiple components SHOULD have same link name
        return []
    
    @staticmethod
    def find_unconnected_links(document: Document, vnets: List[VNET]) -> List[str]:
        """
        Find link names that don't connect to any VNETs.
        
        Args:
            document: Document containing components
            vnets: List of all VNETs
            
        Returns:
            List of link names with no VNET connections
        """
        resolver = LinkResolver()
        link_map = resolver._build_link_map(document)
        link_to_vnets = resolver._map_links_to_vnets(link_map, vnets)
        
        unconnected = []
        # Check all links from link_map
        for link_name in link_map.keys():
            vnet_set = link_to_vnets.get(link_name, set())
            if len(vnet_set) == 0:
                unconnected.append(link_name)
        
        return unconnected
    
    @staticmethod
    def get_link_statistics(document: Document) -> Dict[str, int]:
        """
        Get statistics about link names in document.
        
        Args:
            document: Document to analyze
            
        Returns:
            Dict with statistics (total_components_with_links, unique_link_names, etc.)
        """
        link_map: Dict[str, int] = defaultdict(int)
        total_components = 0
        
        for page in document.get_all_pages():
            for component in page.get_all_components():
                if component.link_name:
                    total_components += 1
                    link_map[component.link_name] += 1
        
        return {
            'total_components_with_links': total_components,
            'unique_link_names': len(link_map),
            'link_usage': dict(link_map)
        }
