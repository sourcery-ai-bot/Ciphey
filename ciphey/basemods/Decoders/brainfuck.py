import re
import time
from typing import Dict, Optional, Tuple

import logging
from rich.logging import RichHandler

from ciphey.iface import Config, Decoder, ParamSpec, T, U, WordList, registry


@registry.register
class Brainfuck(Decoder[str]):
    def decode(self, ctext: T) -> Optional[U]:
        """
        Takes a ciphertext and treats it as a Brainfuck program,
        interpreting it and saving the output as a string to return.

        Brainfuck is a very simple, Turing-complete esoteric language.
        Below is a simplified interpreter that attempts to check whether a
        given ciphertext is a brainfuck program that would output a string.

        A program that can be "decoded" like this is one that:
            * Does not require user input ("," instruction)
            * Includes at least one putchar instruction (".")
            * Does not contain anything but the main 7 instructions,
                (excluding ",") and whitespace

        Details:
            * This implementation wraps the memory pointer for ">" and "<"
            * It is time-limited to 60 seconds, to prevent hangups
            * The program starts with 100 memory cells, chosen arbitrarily
        """

        logging.debug("Attempting brainfuck")

        result = ""
        memory = [0] * 100
        codeptr, memptr = 0, 0  # Instruction pointer and stack pointer
        timelimit = 60  # The timeout in seconds

        bracemap, isbf = self.bracemap_and_check(ctext)

        # If it doesn't appear to be valid brainfuck code
        if not isbf:
            logging.debug("Failed to interpret brainfuck due to invalid characters")
            return None

        # Get start time
        start = time.time()

        while codeptr < len(ctext):

            current = time.time()

            # Return none if we've been running for over a minute
            if current - start > timelimit:
                logging.debug("Failed to interpret brainfuck due to timing out")
                return None

            cmd = ctext[codeptr]

            if cmd == "+":
                memory[memptr] = memory[memptr] + 1 if memory[memptr] < 255 else 0
            elif cmd == "-":
                memory[memptr] = memory[memptr] - 1 if memory[memptr] > 0 else 255
            elif cmd == ">":
                if memptr == len(memory) - 1:
                    memory.append(0)
                memptr += 1

            elif cmd == "<":
                if memptr == 0:
                    memptr = len(memory) - 1
                else:
                    memptr -= 1

            elif cmd == "[" and memory[memptr] == 0:
                codeptr = bracemap[codeptr]

            elif cmd == "]" and memory[memptr]:
                codeptr = bracemap[codeptr]

            elif cmd == ".":
                result += chr(memory[memptr])

            codeptr += 1

        logging.info(f"Brainfuck successful, returning '{result}'")
        return result

    def bracemap_and_check(self, program: str) -> Tuple[Optional[Dict], bool]:
        """
        Create a bracemap of brackets in the program, to compute jmps.
        Maps open -> close brackets as well as close -> open brackets.

        Also returns True if the program is valid Brainfuck code. If False, we
        won't even try to run it.
        """

        open_stack = []
        bracemap = {}
        legal_instructions = {"+", "-", ">", "<", "[", "]", "."}
        legal_count = 0

        # If the program actually outputs anything (contains ".")
        prints = False

        for idx, instruction in enumerate(program):
            # If instruction is brainfuck (without input) or whitespace, it counts
            if instruction in legal_instructions or re.match(r"\s", instruction):
                legal_count += 1

            if not prints and instruction == ".":
                # If there are no "." instructions then this program will not output anything
                prints = True

            elif instruction == "[":
                open_stack.append(idx)

            elif instruction == "]":
                try:
                    opbracket = open_stack.pop()
                    bracemap[opbracket] = idx
                    bracemap[idx] = opbracket
                except IndexError:
                    # Mismatched braces, not a valid program
                    # Closing braces > opening braces
                    return (None, False)

        # 1. All characters are instructions or whitespace
        # 2. There are no extra open braces
        # 3. There is at least one character to be "printed"
        # (result is >=1 in length)
        is_brainfuck = legal_count == len(program) and not open_stack and prints

        return bracemap, is_brainfuck

    @staticmethod
    def priority() -> float:
        # Not uncommon, but not very common either. It's also slow.
        return 0.08

    def __init__(self, config: Config):
        super().__init__(config)
        self.ALPHABET = config.get_resource(self._params()["dict"], WordList)

    @staticmethod
    def getParams() -> Optional[Dict[str, ParamSpec]]:
        return {
            "dict": ParamSpec(
                desc="Brainfuck alphabet (default English)",
                req=False,
                default="cipheydists::list::englishAlphabet",
            )
        }

    @staticmethod
    def getTarget() -> str:
        return "brainfuck"
