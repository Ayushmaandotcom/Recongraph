import requests
from typing import List, Dict, Any
from datetime import datetime

class ERPConnector:
    """Base interface for ERP Integrations."""
    def fetch_ap_invoices(self, since_date: str) -> List[Dict[str, Any]]:
        raise NotImplementedError
        
    def fetch_ar_invoices(self, since_date: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

class SAPConnector(ERPConnector):
    """
    Simulates a connection to an SAP S/4HANA OData API to fetch financial documents
    and transform them into ReconGraph's native JSON format.
    """
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        
    def _get(self, endpoint: str, params: dict) -> dict:
        """Simulates an HTTP GET to SAP."""
        # In a real implementation:
        # response = requests.get(f"{self.base_url}{endpoint}", headers={"APIKey": self.api_key}, params=params)
        # return response.json()
        
        # Mock SAP response for testing
        return {
            "d": {
                "results": [
                    {
                        "AccountingDocument": "5100000001",
                        "CompanyCode": "1000",
                        "FiscalYear": "2026",
                        "DocumentDate": "2026-08-20T00:00:00",
                        "Supplier": "V001",
                        "SupplierName": "ACME Corp",
                        "GSTIN": "27AAACR4321A1Z5",
                        "AmountInCompanyCodeCurrency": "15000.00",
                        "TaxAmount": "2700.00",
                        "TaxCode": "I1"
                    }
                ]
            }
        }

    def fetch_ap_invoices(self, since_date: str) -> List[Dict[str, Any]]:
        """
        Fetches Accounts Payable documents (Purchase Register) from SAP 
        and maps them to ReconGraph's `PurchaseRecord` schema.
        """
        sap_data = self._get("/API_OP_JOURNALENTRY_SRV/A_OperationalAcctgDocItem", {"$filter": f"DocumentDate ge datetime'{since_date}'"})
        
        recongraph_records = []
        for item in sap_data["d"]["results"]:
            recongraph_records.append({
                "record_id": f"SAP_{item['AccountingDocument']}",
                "tenant_id": "erp_synced_tenant",
                "gstin": item["GSTIN"],
                "invoice_number": item["AccountingDocument"],
                "invoice_date": item["DocumentDate"].split("T")[0],
                "taxable_value": float(item["AmountInCompanyCodeCurrency"]),
                "tax_amount": float(item["TaxAmount"]),
                "total_amount": float(item["AmountInCompanyCodeCurrency"]) + float(item["TaxAmount"]),
                "status": "SAVED"
            })
            
        return recongraph_records
