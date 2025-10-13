import zipfile
import os
import glob

zip_folder = "../../results"
output_folder = "../json/10.07-17-07/bank-13"

# Get list of zip files and sort them by date/time in filename
zip_files = sorted(glob.glob(os.path.join(zip_folder, "logs_*.zip")))

idx = 1 
for zip_path in zip_files:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        
        zip_contents = zip_ref.namelist()
        
        # Find the sweep-summary JSON path automatically
        json_paths = [name for name in zip_contents if name.endswith("sweep-summary-1x16MB.json")]
        
        if json_paths:
            json_inside_zip = json_paths[0]  # Take the first match
            
            # Extract JSON content
            json_data = zip_ref.read(json_inside_zip)
            
            # Save to output folder as exp1.json, exp2.json, ...
            output_file = os.path.join(output_folder, f"exp{idx}.json")
            with open(output_file, "wb") as f:
                f.write(json_data)
                
            print(f"Extracted {json_inside_zip} -> {output_file}")
            idx += 1
        else:
            print(f"❌ JSON not found in {zip_path}. Contents: {zip_contents}")

print("✅ All JSON files extracted and renamed.")