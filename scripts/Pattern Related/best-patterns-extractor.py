# This script extracts best patterns of the summary json file of Blacksmith based on total bit flips of each bank in the results
# Attention! The script removes the patterns that don't have any bit flips in any of its `address_mappings` too!
import json

def get_best_pattern_indexes(patterns, total_banks):
    total_patterns_num = len(patterns)
    best_pattern_indexes = []

    for bank_number in range(total_banks):
        highest_bit_flips_num = 0
        print(f"Searching for best patterns for bank: {bank_number}")
        for i in range(total_patterns_num):
            pattern_sum_bitflips = 0
            for addr_map in patterns[i]['address_mappings']:
                if (addr_map['bank_no'] != bank_number):
                    continue
                for bitflip_arr in addr_map['bit_flips']:
                    pattern_sum_bitflips = pattern_sum_bitflips + len(bitflip_arr)
            
            if (pattern_sum_bitflips > highest_bit_flips_num):
                highest_bit_flips_num = pattern_sum_bitflips
                best_pattern_index = i
        if(highest_bit_flips_num != 0):
            best_pattern_indexes.append(best_pattern_index)
        else:
            print(f"Bank: {bank_number} does not exist or has no bitflips in the json file!")

    return best_pattern_indexes

print("Initiating Script...")

total_banks = 32 # 32 banks - you can change based on your needs
output = "best-patterns.json"
input = "../../json/resources/HT1/all-patterns.json"

with open(input, "r", encoding="utf-8") as file:
    data = json.load(file)

new_obj = {
    "metadata": data["metadata"],
    "hammering_patterns": []
}

best_patterns_idx = get_best_pattern_indexes(data['hammering_patterns'], total_banks)
print("Almost there...")
seen = set()
for idx in best_patterns_idx:
    if idx not in seen:
        new_obj["hammering_patterns"].append(data["hammering_patterns"][idx])
        seen.add(idx)

with open(output, "w", encoding="utf-8") as f:
    json.dump(new_obj, f, indent=4)

print(f"Done! Output is saved in '{output}'")