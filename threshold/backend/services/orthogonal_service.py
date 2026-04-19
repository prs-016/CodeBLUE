import logging
from typing import Dict, Any
import requests

from config import settings

logger = logging.getLogger(__name__)

class OrthogonalService:
    """
    Integrates with orthogonal.com API ecosystem to augment physical climate indices 
    with financial, meteorological, and enterprise impact layers.
    
    Integrated APIs:
    - Precip: High-resolution watershed and precipitation modeling.
    - Openmart: B2B intelligence and enterprise asset exposure.
    - Nyne: Synthesized predictive risk and market analytics.
    """
    
    @classmethod
    def _get_headers(cls) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.orthogonal_api_key}",
            "Content-Type": "application/json"
        }

    @classmethod
    def _fetch_precip_forecast(cls, region_id: str) -> Dict[str, Any]:
        """
        Query Orthogonal's Precip API for localized weather extremum and flood risk.
        Endpoint: https://www.orthogonal.com/discover/precip
        """
        response = requests.get(
            "https://www.orthogonal.com/discover/precip",
            headers=cls._get_headers(),
            params={"region_id": region_id}
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def _fetch_openmart_enterprises(cls, region_id: str) -> Dict[str, Any]:
        """
        Query Orthogonal's Openmart API for local supply chain and SMB/Corporate disruption impact.
        Endpoint: https://www.orthogonal.com/discover/openmart
        """
        response = requests.get(
            "https://www.orthogonal.com/discover/openmart",
            headers=cls._get_headers(),
            params={"region_id": region_id}
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def _fetch_nyne_risk_synthesis(cls, physical_score: float, precip_data: dict, openmart_data: dict) -> Dict[str, Any]:
        """
        Query Orthogonal's Nyne API to ingest raw physical and market variables and 
        compute a blended institutional risk premium / financial severity index.
        Endpoint: https://www.orthogonal.com/discover/nyne
        """
        response = requests.post(
            "https://www.orthogonal.com/discover/nyne",
            headers=cls._get_headers(),
            json={
                "physical_score": physical_score,
                "precip_data": precip_data,
                "openmart_data": openmart_data
            }
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def fetch_orthogonal_risk_premium(cls, region_id: str, physical_score: float = 6.5) -> Dict[str, Any]:
        """
        Primary interface that aggregates the 3 Orthogonal APIs (Precip, Openmart, Nyne)
        into the main THRESHOLD intelligence pipeline.
        """
        logger.info(f"Querying live Orthogonal API ecosystem for region: {region_id}")
        
        precip = cls._fetch_precip_forecast(region_id)
        openmart = cls._fetch_openmart_enterprises(region_id)
        nyne = cls._fetch_nyne_risk_synthesis(physical_score, precip, openmart)
        
        # We assume the Nyne API returns a dictionary containing a synthesized risk score 
        return {
            "region_id": region_id,
            "orthogonal_payload": {
                "precip_meteorology": precip,
                "openmart_exposure": openmart,
                "nyne_evaluation": nyne
            },
            "final_orthogonal_risk_index": nyne.get("nyne_synthesized_risk_index", nyne.get("risk_index")),
            "status": "success"
        }
