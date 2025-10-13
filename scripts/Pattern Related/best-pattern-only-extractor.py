# This script extracts only the best pattern of the summary json file of Blacksmith based on total bit flips.
import json

def get_best_pattern_index(patterns):
    total_patterns_num = len(patterns)
    highest_bit_flips_num = 0
    for i in range(total_patterns_num):
        pattern_sum_bitflips = 0
        for addr_map in patterns[i]['address_mappings']:
            for bitflip_arr in addr_map['bit_flips']:
                pattern_sum_bitflips = pattern_sum_bitflips + len(bitflip_arr)
        
        if (pattern_sum_bitflips > highest_bit_flips_num):
            highest_bit_flips_num = pattern_sum_bitflips
            best_pattern_index = i

    return best_pattern_index

output = "best-pattern-only.json"
input = "../../json/resources/HT1/best-patterns.json"

with open(input, "r", encoding="utf-8") as file:
    data = json.load(file)

new_obj = {
    "metadata": data["metadata"],
    "hammering_patterns": []
}

best_pattern_idx = get_best_pattern_index(data['hammering_patterns'])
new_obj['hammering_patterns'].append(data['hammering_patterns'][best_pattern_idx])

with open(output, "w", encoding="utf-8") as f:
    json.dump(new_obj, f, indent=4)

print(f"Done! Output is saved in '{output}'")