import os
import pandas as pd

from collections import defaultdict


class RockEvalData:
    """TODO Docstring
    """

    def __init__(self, sample_name, re_version, input_folder):
        """
        :param sample_name: TODO
        :param re_version: TODO
        :param input_folder: TODO 
        """
        if re_version not in ("RE6", "RE7"):
            raise Exception("Only 'RE6' and 'RE7' are admitted re_version values.")
        self.sample_name = sample_name
        self.re_version = re_version
        self.input_folder = input_folder
        self._metadata, self._data = self._parse()
    
    @staticmethod
    def parse_rock_eval(path):
        """TODO add Docstring with for instance the format of the file to parse?
        """
        metadata = defaultdict(dict)
        data = defaultdict(list)

        # S00 or B00
        filetype = path.split(".")[1]
        
        with open(path, "r") as f:
            reading_metadata = True
            for line in f.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                new_key = line.startswith("[") and line.endswith("]")
                if new_key:
                    key = line[1:-1]
                    if filetype == "S00" or (filetype == "B00" and key == "Curves Pyro"):
                        reading_metadata = False
                elif reading_metadata:
                    if "=" not in line: # non-formatted metadata
                        try:
                            metadata[key]["Extra"] = metadata[key]["Extra"] + [line]
                        except KeyError:
                            metadata[key]["Extra"] = [line]
                    else:
                        key_inner, value = line.split("=")
                    metadata[key][key_inner] = value
                else:
                    data[key].append(line.split("\t"))
        return metadata, data

    def _parse(self):
        """TODO add docstring
        """
        if self.re_version == "RE6":
            metadata_path = os.path.join(self.input_folder, self.sample_name + ".R00")
            data_path = os.path.join(self.input_folder, self.sample_name + ".S00")
            metadata, _ = self.parse_rock_eval(metadata_path)
            _, data = self.parse_rock_eval(data_path)
        elif self.re_version == "RE7":
            path = os.path.join(self.input_folder, self.sample_name + ".B00")
            metadata, data = self.parse_rock_eval(path)
        else:
            return
        return metadata, data
        

    def _extract_curves(self):
        columns_pyr = [
            "time",
            "T",
            "FID",
            "CO",
            "CO2"
        ]
        if self.re_version == "RE6":
            curves_pyr = self._data["Curves pyro"]
        elif self.re_version == "RE7":
            curves_pyr = self._data["Curves Pyro"]
            columns_pyr.append("SO2")
        else:
            return
        
        curves_pyr = pd.DataFrame(curves_pyr, columns=columns_pyr)

        columns_oxi = [
            "time",
            "T",
            "CO",
            "CO2"
        ]
        if self.re_version == "RE6":
            curves_oxi = self._data["Curves oxi"]
        elif self.re_version == "RE7":
            curves_oxi = self._data["Curves Oxi"]
            columns_oxi.append("SO2")
        else:
            return
        curves_oxi = pd.DataFrame(curves_oxi, columns=columns_oxi)
        
        return {"pyrolysis": curves_pyr.astype(float), "oxidation": curves_oxi.astype(float)}

    def _normalize_curves(self, raw_curves):
        if self.re_version not in ('RE6', 'RE7'):
            return

        curves_pyr = raw_curves["pyrolysis"].copy()
        curves_oxi = raw_curves["oxidation"].copy()
        metadata = self._metadata
        
        baseline = {}
        weight = float(metadata["Param"]["Quant"])
        if self.re_version == "RE6":
            kfid = float(metadata["Standard"]["KFid"])
            baseline["FID"] = float(metadata["Curs manu_1"]["Base"])
            baseline["CO_pyr"] = float(metadata["Curs manu_2"]["Base"])
            baseline["CO2_pyr"] = float(metadata["Curs manu_3"]["Base"]) 
            baseline["CO_oxi"] = float(metadata["Curs manu_4"]["Base"])
            baseline["CO2_oxi"] = float(metadata["Curs manu_5"]["Base"]) 
        
        elif self.re_version == "RE7":
            kfid = float(metadata["Standard"]["K_FID"])

            def baseline_RE7(metadata, key):
                bl = metadata["base ligne"][key]
                if len(bl) == 0:
                    return 0
                else:
                    return float(bl)
                    
            baseline["FID"] = baseline_RE7(metadata, "LB_FID")
            baseline["CO_pyr"] = baseline_RE7(metadata, "LB_CO_P")
            baseline["CO2_pyr"] = baseline_RE7(metadata, "LB_CO2_P")
            baseline["SO2_pyr"] = baseline_RE7(metadata, "LB_SO2_P")
            baseline["CO_oxi"] = baseline_RE7(metadata, "LB_CO_O")
            baseline["CO2_oxi"] = baseline_RE7(metadata, "LB_CO2_O")
            baseline["SO2_oxi"] = baseline_RE7(metadata, "LB_SO2_O")
        
        curves_pyr["FID"] = curves_pyr["FID"].apply(lambda x: x - baseline["FID"])
        curves_pyr["CO"] = curves_pyr["CO"].apply(lambda x: x - baseline["CO_pyr"])
        curves_oxi["CO"] = curves_oxi["CO"].apply(lambda x: x - baseline["CO_oxi"])
        curves_pyr["CO2"] = curves_pyr["CO2"].apply(lambda x: x - baseline["CO2_pyr"])
        curves_oxi["CO2"] = curves_oxi["CO2"].apply(lambda x: x - baseline["CO2_oxi"])
        if self.re_version == "RE7":
            curves_pyr["SO2"] = curves_pyr["SO2"].apply(lambda x: x - baseline["SO2_pyr"])
            curves_oxi["SO2"] = curves_oxi["SO2"].apply(lambda x: x - baseline["SO2_oxi"])

        def normalize_HC(x):
            return (kfid * 100 * 0.83 * x) / weight
        
        def normalize_gas(x, mass_ratio):
            return (mass_ratio * x) / (1000 * weight)

        curves_pyr["FID"] = curves_pyr["FID"].apply(normalize_HC)
        curves_pyr["CO"] = curves_pyr["CO"].apply(lambda x: normalize_gas(x, 12 / 28))
        curves_oxi["CO"] = curves_oxi["CO"].apply(lambda x: normalize_gas(x, 12 / 28))
        curves_pyr["CO2"] = curves_pyr["CO2"].apply(lambda x: normalize_gas(x, 12 / 44))
        curves_oxi["CO2"] = curves_oxi["CO2"].apply(lambda x: normalize_gas(x, 12 / 44))
        if self.re_version == "RE7":
            curves_pyr["SO2"] = curves_pyr["SO2"].apply(lambda x: normalize_gas(x, 32 / 64))
            curves_oxi["SO2"] = curves_oxi["SO2"].apply(lambda x: normalize_gas(x, 32 / 64))

        return {"pyrolysis": curves_pyr, "oxidation": curves_oxi}
        
    def get_metadata(self):
        return self._metadata

    def get_curves(self, normalized=True):
        raw_curves = self._extract_curves()
        if normalized:
            return self._normalize_curves(raw_curves)
        return raw_curves