import os
import json
import matplotlib.pyplot as plt

from rock_eval_data import RockEvalData

# To be replaced with custom values
input_folder = "example_data"
output_folder = "example_treated_data"
sample_name = "example"
re_version = "RE6"      # valid values are 'RE6' and 'RE7'

os.makedirs(output_folder, exist_ok=True)

data = RockEvalData(sample_name, re_version, input_folder)

# retrieve curves data and save as .csv
curves = data.get_curves()
curves["pyrolysis"].to_csv(os.path.join(output_folder, sample_name + "_pyr.csv"), index=False)
curves["oxidation"].to_csv(os.path.join(output_folder, sample_name + "_oxi.csv"), index=False)

# retrieve metadata and save as .json
metadata = data.get_metadata()
with open(os.path.join(output_folder, sample_name + "_metadata.json"), "w") as outfile:
    json.dump(metadata, outfile, indent=4)

# plot curves
fig, axs = plt.subplots(2, 4, figsize=(16, 8))
for i, f in enumerate(["T", "FID", "CO", "CO2"]):
    axs[0][i].plot(curves["pyrolysis"]["time"], curves["pyrolysis"][f])
    axs[0][i].set_xlabel("time")
    axs[0][i].set_ylabel(f)
    axs[0][i].set_title(f + " Pyrolysis")
    axs[0][i].grid(True)
for j, f in enumerate(["T", "CO", "CO2"]):
    axs[1][j].plot(curves["oxidation"]["time"], curves["oxidation"][f])
    axs[1][j].set_xlabel("time")
    axs[1][j].set_ylabel(f)
    axs[1][j].set_title(f + " Oxidation")
    axs[1][j].grid(True)
plt.tight_layout()
plt.show()