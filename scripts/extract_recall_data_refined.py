import pandas as pd
import os

# Define paths
data_dir = "../data"
output_dir = "../output"

# Define recall data structure
recall_data = []
seen_fa_codes = set()  # Track FA codes globally across all files

# Extract from Excel
def extract_from_excel(excel_path):
    recalls = []
    try:
        # Load rappelCompagne sheet instead of TUNISIA (TN)
        df = pd.read_excel(excel_path, sheet_name="rappelCompagne")
        
        for _, row in df.iterrows():
            if pd.notna(row.iloc[3]) and str(row.iloc[3]).isdigit():
                brand = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else ""
                if brand in ['CGDR', 'FO', 'FT']:
                    fa_code = str(row.iloc[3]).strip()
                    
                    # Only add if fa_code not already seen in any file
                    if fa_code not in seen_fa_codes:
                        recall = {
                            "fa_type": str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else "",
                            "fa_code": fa_code,
                            "car_parked": str(row.iloc[6]) if pd.notna(row.iloc[6]) else ""
                        }
                        recalls.append(recall)
                        seen_fa_codes.add(fa_code)
    except Exception as e:
        print(f"Error processing {excel_path}: {e}")
    return recalls

# Main execution
if __name__ == "__main__":
    excel_files = [f for f in os.listdir(data_dir) if f.endswith(".xlsx") and not f.startswith('~')]
    
    for excel_file in excel_files:
        recalls = extract_from_excel(os.path.join(data_dir, excel_file))
        recall_data.extend(recalls)
    
    # Save to local CSV
    df = pd.DataFrame(recall_data)
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(os.path.join(output_dir, "recall_data.csv"), index=False, encoding="utf-8")
    print("Data extracted and saved to local CSV.")
