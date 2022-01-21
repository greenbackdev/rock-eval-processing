import os
from rock_eval_data import RockEvalData
import json

input_folder = "test_data"
output_folder = "test_treated_data"
os.makedirs(output_folder, exist_ok=True)

for sample_name, version in zip(["test_RE6", "test_RE7"], ["RE6", "RE7"]):
    data = RockEvalData(sample_name, version, input_folder)
    curves = data.get_curves()
    curves["pyrolysis"].to_csv(os.path.join(output_folder, sample_name+"_pyr.csv"), index=False)
    curves["oxidation"].to_csv(os.path.join(output_folder, sample_name+"_oxi.csv"), index=False)

    metadata = data.get_metadata()
    with open(os.path.join(output_folder, sample_name+"_metadata.json"), "w") as outfile:
        json.dump(metadata, outfile, indent=4)
