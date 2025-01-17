import re
from typing import Dict, List, Optional

import logging
from rich.logging import RichHandler

from ciphey.iface import Config, Cracker, CrackInfo, CrackResult, ParamSpec, registry


@registry.register
class Xandy(Cracker[str]):
    def getInfo(self, ctext: str) -> CrackInfo:
        return CrackInfo(
            success_likelihood=0.1,
            success_runtime=1e-5,
            failure_runtime=1e-5,
        )

    @staticmethod
    def binary_to_ascii(variant):
        # Convert the binary string to an integer with base 2
        binary_int = int(variant, 2)
        byte_number = binary_int.bit_length() + 7 // 8

        # Convert the resulting int to a bytearray and then decode it to ASCII text
        binary_array = binary_int.to_bytes(byte_number, "big")
        try:
            ascii_text = binary_array.decode()
            logging.debug(f"Found possible solution: {ascii_text[:32]}")
            return ascii_text
        except UnicodeDecodeError as e:
            logging.debug(f"Failed to crack X-Y due to a UnicodeDecodeError: {e}")
            return ""

    @staticmethod
    def getTarget() -> str:
        return "xandy"

    def attemptCrack(self, ctext: str) -> List[CrackResult]:
        """
        Checks an input if it only consists of two or three different letters.
        If this is the case, it attempts to regard those letters as
        0 and 1 (with the third characters as an optional delimiter) and then
        converts it to ASCII text.
        """
        logging.debug("Attempting X-Y replacement")
        variants = []
        result = []

        # Convert the ctext to all-lowercase and regex-match & replace all whitespace
        ctext = re.sub(r"\s+", "", ctext.lower(), flags=re.UNICODE)

        # cset contains every unique value in the ctext
        cset = list(set(list(ctext)))
        cset_len = len(cset)

        if not 1 < cset_len < 4:
            # We only consider inputs with two or three unique values
            logging.debug(
                "Failed to crack X-Y due to not containing two or three unique values"
            )
            return None

        logging.debug(f"String contains {cset_len} unique values: {cset}")

        # In case of three unique values, we regard the least frequent character as the delimiter
        if cset_len == 3:
            # Count each unique character in the set to determine the least frequent one
            counting_list = [ctext.count(char) for char in cset]
            val, index = min((val, index) for (index, val) in enumerate(counting_list))
            delimiter = cset[index]
            logging.debug(
                f"{delimiter} occurs {val} times and is the probable delimiter"
            )
            # Remove the delimiter from the ctext and compute new cset
            ctext = ctext.replace(delimiter, "")
            cset = list(set(list(ctext)))

        # Form both variants of the substitution
        for i in range(2):
            if i:
                variants.append(ctext.replace(cset[0], "1").replace(cset[1], "0"))
            else:
                variants.append(ctext.replace(cset[0], "0").replace(cset[1], "1"))

        candidates = [
            self.binary_to_ascii(variant).strip("\x00") for variant in variants
        ]

        for i, candidate in enumerate(candidates):
            if candidate != "":
                keyinfo = f"{cset[0]} -> {i} & {cset[1]} -> {int(not i)}"
                result.append(CrackResult(value=candidate, key_info=keyinfo))
                logging.debug(f"X-Y cracker - Returning results: {result}")
                return result

    @staticmethod
    def getParams() -> Optional[Dict[str, ParamSpec]]:
        return {
            "expected": ParamSpec(
                desc="The expected distribution of the plaintext",
                req=False,
                config_ref=["default_dist"],
            )
        }

    def __init__(self, config: Config):
        super().__init__(config)
        self.expected = config.get_resource(self._params()["expected"])
        self.cache = config.cache
