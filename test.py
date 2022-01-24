import os
from rock_eval_data import RockEvalData
import json
import matplotlib.pyplot as plt

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

# plot curves
fig, axs = plt.subplots(2, 4, figsize=(16, 8))
for sample in samples:
    for i, f in enumerate(["T", "FID", "CO", "CO2"]):
        axs[0][i].plot(all_curves[sample]["pyrolysis"]["time"], all_curves[sample]["pyrolysis"][f], label=sample)
        axs[0][i].set_xlabel("time")
        axs[0][i].set_ylabel(f)
        axs[0][i].set_title(f + " Pyrolysis")
        axs[0][i].grid(True)
    for j, f in enumerate(["T", "CO", "CO2"]):
        axs[1][j].plot(all_curves[sample]["oxidation"]["time"], all_curves[sample]["oxidation"][f], label=sample)
        axs[1][j].set_xlabel("time")
        axs[1][j].set_ylabel(f)
        axs[1][j].set_title(f + " Oxidation")
        axs[1][j].grid(True)

handles, labels = axs[1][2].get_legend_handles_labels()
lgd = axs[1][3].legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5,1))
axs[1][3].axis('off')
plt.tight_layout()
plt.show()