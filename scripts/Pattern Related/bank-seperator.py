# This script seperates each `address_mappings` and saves it into a new pattern and stores the data based on the banks.
import json
import os

def get_best_pattern_index(patterns):
    total_patterns_num = len(patterns)
    highest_bit_flips_num = 0
    for i in range(total_patterns_num):
        bank_sum_bitflips = 0
        for addr_map in patterns[i]['address_mappings']:
            for bitflip_arr in addr_map['bit_flips']:
                bank_sum_bitflips = bank_sum_bitflips + len(bitflip_arr)
        
        if (bank_sum_bitflips > highest_bit_flips_num):
            highest_bit_flips_num = bank_sum_bitflips
            best_pattern_index = i

    return best_pattern_index

total_banks = 32 # 32 banks - you can change based on your needs
input = "./pattern-b6b7.json"
root_dir_name = "seperated-banks"

os.makedirs(root_dir_name, exist_ok=True)

with open(input, "r", encoding="utf-8") as file:
    data = json.load(file)

for bank in range(total_banks):

    for pattern_idx, pattern in enumerate(data['hammering_patterns']):
        does_bank_exist = False
        bank_empty_biflips = True
        new_obj = {
            "metadata": data["metadata"],
            "hammering_patterns": []
        }
        for addr_mapping in pattern['address_mappings']:
            if (addr_mapping['bank_no'] == bank):
                does_bank_exist = True
                for bit_flip_arr in addr_mapping['bit_flips']:
                    bank_empty_biflips = False
                    output = f"{root_dir_name}/bank{bank}/pattern{pattern_idx}.json"
                    os.makedirs(f"{root_dir_name}/bank{bank}", exist_ok=True)
                    filtered_pattern = pattern.copy()
                    filtered_pattern["address_mappings"] = [addr_mapping]
                    new_obj["hammering_patterns"].append(filtered_pattern)
                    with open(output, "w", encoding="utf-8") as f:
                        json.dump(new_obj, f, indent=4)
                    break
        if(not bank_empty_biflips and does_bank_exist):
                break

print(f"Done! Output is saved in '{root_dir_name}' path!")