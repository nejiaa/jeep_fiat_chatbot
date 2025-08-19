import pdfplumber
import pandas as pd
import os
import re

# Define paths
data_dir = "../data/data_entretien"
output_dir = "../output"

# Define maintenance data structure
maintenance_data = []

# Extract from PDF
def extract_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if not text:
                print(f"No extractable text on page {page_num} of {pdf_path}. Consider OCR if scanned.")
                continue
            
            print(f"Raw text from page {page_num} (first 500 chars): {text[:500]}...")
            
            # Extract visit data across pages
            visite_matches = re.finditer(r"Visite\s*(\d+\.?\d*\s*Kms?)\s*[\s\S]*?(Total\s*\(MO\+PDR\)\s*TTC\s*([\d,.]+)|$)", text, re.IGNORECASE)
            for match in visite_matches:
                visite_kms = match.group(1).strip()
                total_ttc = match.group(3).replace(",", ".").strip() if match.group(3) else "0"
                
                maintenance = {
                    "visite_kms": visite_kms,
                    "références": "",
                    "désignations": "",
                    "quantité": "",
                    "prix_unitaire_ht": "",
                    "prix_total_pdr_ht": "",
                    "mo_ht": "",
                    "remise": "",
                    "total_mo_pdr_net_ht": "",
                    "total_mo_pdr_ttc": total_ttc
                }
                
                # Extract line items in the section
                section_start = match.start()
                next_visite_pos = text.find("Visite", match.end()) if match.end() < len(text) else len(text)
                section_text = text[section_start:next_visite_pos] if next_visite_pos != -1 else text[section_start:]
                
                # Flexible line item extraction
                line_items = re.finditer(r"(\d+[A-Z0-9]+)\s+([^\n]+?)\s+(\d+)\s+([\d,.]+)", section_text)
                for item in line_items:
                    maintenance["références"] += item.group(1) + "; "
                    maintenance["désignations"] += item.group(2).strip() + "; "
                    maintenance["quantité"] += item.group(3) + "; "
                    maintenance["prix_unitaire_ht"] += item.group(4).replace(",", ".") + "; "
                
                # Clean up
                for key in ["références", "désignations", "quantité", "prix_unitaire_ht"]:
                    maintenance[key] = maintenance[key].rstrip("; ") if maintenance[key] else ""
                
                # Extract additional fields
                mo_ht_match = re.search(r"MO\s*HT\s*([\d,.]+)", section_text, re.IGNORECASE)
                maintenance["mo_ht"] = mo_ht_match.group(1).replace(",", ".") if mo_ht_match else ""
                
                remise_match = re.search(r"Remise\s*([\d,.]+%?)", section_text, re.IGNORECASE)
                maintenance["remise"] = remise_match.group(1) if remise_match else "0%"
                
                total_net_match = re.search(r"Total\s*\(MO\+PDR\)\s*net\s*HT\s*([\d,.]+)", section_text, re.IGNORECASE)
                maintenance["total_mo_pdr_net_ht"] = total_net_match.group(1).replace(",", ".") if total_net_match else ""
                
                maintenance_data.append(maintenance)
                print(f"Extracted data for {visite_kms} from page {page_num} of {pdf_path}")

    return len(maintenance_data) > 0

# Main execution
if __name__ == "__main__":
    pdf_files = [f for f in os.listdir(data_dir) if f.endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in", data_dir)
    for pdf_file in pdf_files:
        success = extract_from_pdf(os.path.join(data_dir, pdf_file))
        if not success:
            print(f"No data extracted from {pdf_file}. Check file content or format.")
    
    # Save to local CSV
    if maintenance_data:
        df = pd.DataFrame(maintenance_data)
        os.makedirs(output_dir, exist_ok=True)
        df.to_csv(os.path.join(output_dir, "maintenance_data.csv"), index=False, encoding="utf-8")
        print("Maintenance data extracted and saved to local CSV.")
    else:
        print("No maintenance data extracted. CSV not created.")