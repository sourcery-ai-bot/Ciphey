from typing import Dict, Optional

import logging
from rich.logging import RichHandler

from ciphey.iface import Config, Decoder, ParamSpec, T, Translation, U, registry


@registry.register
class Galactic(Decoder[str]):
    def decode(self, ctext: T) -> Optional[U]:
        """
        Takes a string written in the 'Standard Galactic Alphabet'
        (aka Minecraft Enchanting Table Symbols) and translates it to ASCII text.
        """
        logging.debug("Attempting Standard Galactic Alphabet decoder")

        # To avoid complications, only move forward with the decoding if we can
        # reasonably assume that the input string is written in the galactic alphabet
        galactic_matches = sum(
            symbol in ctext and symbol not in ["!", "|"]
            for symbol in self.GALACTIC_DICT.keys()
        )

        if galactic_matches == 0:
            logging.debug(
                "No matching galactic alphabet letters found. Skipping galactic decoder"
            )
            return None
        logging.debug(f"{galactic_matches} galactic alphabet letters found. ")

        result = ""
        # Take out the problematic characters consisting of multiple symbols
        ctext = (
            ctext.replace("||", "|")
            .replace("/", "")
            .replace("¡", "")
            .replace(" ̣ ", "")
            .replace("̇", "x")
        )
        logging.debug(f"Modified string is {ctext}")

        for letter in ctext:
            if letter in self.GALACTIC_DICT.keys():
                # Match every letter of the input to its galactic counterpoint
                result += self.GALACTIC_DICT[letter]
            else:
                # If the current character is not in the defined alphabet,
                # just accept it as-is (useful for numbers, punctuation, etc.)
                result += letter
        # Remove the trailing space (appearing as a leading space)
        # from the x that results from the diacritic replacement
        result = result.replace("x ", "x")
        logging.debug(f"Decoded string is {result}")
        return result

    @staticmethod
    def priority() -> float:
        # Not expected to show up often, but also very fast to check.
        return 0.01

    def __init__(self, config: Config):
        super().__init__(config)
        self.GALACTIC_DICT = config.get_resource(self._params()["dict"], Translation)

    @staticmethod
    def getParams() -> Optional[Dict[str, ParamSpec]]:
        return {
            "dict": ParamSpec(
                desc="The galactic alphabet dictionary to use",
                req=False,
                default="cipheydists::translate::galactic",
            )
        }

    @staticmethod
    def getTarget() -> str:
        return "galactic"
