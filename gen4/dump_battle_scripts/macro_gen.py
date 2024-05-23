from argparse import ArgumentParser
import inspect

import consts

from consts import (
    MessageTag,
    PLAT_COMMANDS,
    HGSS_COMMANDS,
)

def arg_list(params: list) -> str:
    return ', '.join(list(map(lambda i: f'arg_{i}', range(len(params)))))

ARGP = ArgumentParser(
    description='Generates macro definitions for Gen4 byte-code sequences'
)
ARGP.add_argument('-g', '--game',
                  choices=['pt', 'hg'],
                  help='which command dictionary to use for macro generation',
                  required=True)

args = ARGP.parse_args()
match args.game:
    case 'pt':
        commands = PLAT_COMMANDS
    case 'hg':
        commands = HGSS_COMMANDS
    case _:
        raise ValueError(f'Unrecognized value for game: {args.game}')

lines = [
    '.ifndef ASM_BATTLE_SCRIPT_INC',
    '.set ASM_BATTLE_SCRIPT_INC, 1',
    '.option alignment off',
    '.include "asm/include/interop_macros.inc"',
    '.include "asm/include/abilities.inc"',
    '.include "asm/include/hold_item_effects.inc"',
    '.include "asm/include/items.inc"',
    '.include "asm/include/move_effects.inc"',
    '.include "asm/include/moves.inc"',
    '.include "asm/include/species.inc"',
    '.include "asm/include/battle_constants.inc"', # also generated here
    '',
]

for i, cmd in enumerate(commands):
    if "PrintMessage" in cmd.name or "PrintGlobalMessage" in cmd.name or "BufferMessage" in cmd.name:
        for j in [6]:
            currLine = f'    .macro {cmd.name} {arg_list(cmd.params)}'
            argList = ""
            if j > 1:
                currLine = currLine + f", arg_2"
                argList = argList + f"    .long \\arg_2"
                for k in range(1, j):
                    currLine = currLine + f", arg_{k+2}"
                    argList = argList + f", \\arg_{k+2}"
            elif j == 1:
                currLine = currLine + f", arg_3"
                argList = argList + f"    .long \\arg_2"
            lines.append(currLine)
            lines.append(f'    .long {i}')
            for k in range(len(cmd.params)):
                lines.append(f'    .long \\arg_{k}')
            if (argList != ""):
                lines.append(argList)
            lines.append('    .endm\n')
    elif "BufferLocalMessage" in cmd.name:
        for j in [6]:
            currLine = f'    .macro {cmd.name} {arg_list(cmd.params)}'
            argList = ""
            if j > 1:
                currLine = currLine + f", arg_3"
                argList = argList + f"    .long \\arg_3"
                for k in range(1, j):
                    currLine = currLine + f", arg_{k+3}"
                    argList = argList + f", \\arg_{k+3}"
            elif j == 1:
                currLine = currLine + f", arg_4"
                argList = argList + f"    .long \\arg_3"
            lines.append(currLine)
            lines.append(f'    .long {i}')
            for k in range(len(cmd.params)):
                lines.append(f'    .long \\arg_{k}')
            if (argList != ""):
                lines.append(argList)
            lines.append('    .endm\n')
    else:
        if cmd.params:
            lines.append(f'    .macro {cmd.name} {arg_list(cmd.params)}')
        else:
            lines.append(f'    .macro {cmd.name}')
        lines.append(f'    .long {i}')

        for j in range(len(cmd.params)):
            lines.append(f'    .long \\arg_{j}')
        lines.append('    .endm\n')

lines.append(f'.endif')
lines.append(f'')

with open('battle_commands.inc', 'w') as fout:
    fout.write('\n'.join(lines))

my_module_class_names = [
    [name, clazz] for name, clazz in inspect.getmembers(consts, inspect.isclass)
]

lines = [
    '.ifndef GUARD_BATTLE_CONSTANTS',
    '.definelabel GUARD_BATTLE_CONSTANTS, 0',
    '',
]

for clas in my_module_class_names:
    if "enum" in str(clas) and "auto" not in str(clas):
        for i, value in enumerate(clas[1]):
            lines.append(f'.equ {str(value).split(".")[1]}, 0x{value.value:X}')
        lines.append(f'')
        lines.append(f'')

lines.append(f'.endif')
lines.append(f'')

with open('battle_constants.inc', 'w') as fout:
    fout.write('\n'.join(lines))
