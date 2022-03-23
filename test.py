import os
import json
import matplotlib.pyplot as plt

from rock_eval_data import RockEvalData

input_folder = "test_data"
output_folder = "test_treated_data"
os.makedirs(output_folder, exist_ok=True)

all_curves ={}
samples = ["test_RE6", "test_RE7"]
re_versions = ["RE6", "RE7"]

for sample_name, version in zip(samples, re_versions):
    all_curves[sample_name] = {}
    data = RockEvalData(sample_name, version, input_folder)
    curves = data.get_curves()
    curves["pyrolysis"].to_csv(os.path.join(output_folder, sample_name+"_pyr.csv"), index=False)
    curves["oxidation"].to_csv(os.path.join(output_folder, sample_name+"_oxi.csv"), index=False)
    all_curves[sample_name]["pyrolysis"] = curves["pyrolysis"]
    all_curves[sample_name]["oxidation"] = curves["oxidation"]

    metadata = data.get_metadata()
    with open(os.path.join(output_folder, sample_name+"_metadata.json"), "w") as outfile:
        json.dump(metadata, outfile, indent=4)
