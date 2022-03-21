import os
import pandas as pd

from collections import defaultdict


class RockEvalData:
    """
    A class used to represent Rock Eval data of a sample.
    """

    def __init__(self, sample_name: str, re_version: str, input_folder: str):
        """
        :param sample_name: The name of the sample. It must be the name of the raw data file(s).
        :param re_version: The RockEval instrument version. Admitted values are 'RE6' and 'RE7'.
        :param input_folder: Path to the folder containing the raw RockEval data.
        :type sample_name: str
        :type re_version: str
        :type input_folder: str
        """
        if re_version not in ("RE6", "RE7"):
            raise Exception("Only 'RE6' and 'RE7' are admitted re_version values.")
        self.sample_name = sample_name
        self.re_version = re_version
        self.input_folder = input_folder
        self._metadata, self._data = self._parse()
    
    @staticmethod
    def parse_rock_eval(path: str):
        """
        Parses the raw RockEval data and metadata file(s).

        Three types of file extensions are accepted:
            - .S00: RE6 data
            - .R00: RE6 metadata
            - .B00: RE7 data and metadata
        
        :param path: Path to the file. Accepted file extensions are .S00, .R00, .B00.
        :returns: tuple (metadata, data)
        :rtype tuple
        """

        metadata = defaultdict(dict)
        data = defaultdict(list)

        filetype = path.split(".")[1]
        if filetype not in ["R00", "S00", "B00"]:
            raise Exception("Only '.R00', '.S00' and '.B00' are admitted file extensions.")
        
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
        """Parses the raw RockEval data and metadata file(s).

        Returns a tuple containing the metadata and the data as dictionaries.

        :returns: tuple (metadata, data)
        :rtype tuple
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
        """Extracts the pyrolysis and oxidation curves from the data dictionary.

        Returns a dictionary of pandas.DataFrame() objects (one DataFrame for pyrolysis
        and one for oxidation).

        :returns: RockEval pyrolysis and oxidation curves
        :rtype dict
        """

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

    def _normalize_curves(self, raw_curves: dict):
        """Normalizes the Pyrolysis and Oxidation curves with respect to the the sample mass.

        :param raw_curves: RockEval pyrolysis and oxidation curves
        :type raw_curves: dict
        :returns: Normalized RockEval pyrolysis and oxidation curves
        :rtype dict
        """

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
        """Returns the sample's metadata.

        :returns: metadata
        :rtype: dict
        """

        return self._metadata

    def get_curves(self, normalized=True):
        """Returns the Pyrolysis and Oxidation curves.

        :param normalized: if True, the curves are normalized with respect to the sample's mass (default is True).
        :type param: bool
        :returns: RockEval pyrolysis and oxidation curves
        :rtype dict
        """

        raw_curves = self._extract_curves()
        if normalized:
            return self._normalize_curves(raw_curves)
        return raw_curves