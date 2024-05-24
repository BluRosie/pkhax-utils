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
# manual cases because not all args are encoded or are weird
    if "PrintMessage" in cmd.name or "PrintGlobalMessage" in cmd.name or "BufferMessage" in cmd.name:
        currLine = f"""    .macro {cmd.name} msg_id, tag, arg_0, arg_1, arg_2, arg_3, arg_4, arg_5
    .long {i}
    .long \\msg_id
    .long \\tag
    .if \\tag > TAG_NONE
        .long \\arg_0
        .if \\tag > TAG_TRNAME
            .long \\arg_1
            .if \\tag > TAG_TRCLASS_TRNAME
                .long \\arg_2
                .if \\tag > TAG_TRCLASS_TRNAME_ITEM
                    .long \\arg_3
                    .if \\tag > TAG_TRCLASS_TRNAME_TRCLASS_TRNAME
                        .long \\arg_4
                        .long \\arg_5
                    .endif
                .endif
            .endif
        .endif
    .endif
    .endm
"""
        lines.append(currLine)
    elif "BufferLocalMessage" in cmd.name:
        currLine = f"""    .macro {cmd.name} battler, msg_id, tag, arg_0, arg_1, arg_2, arg_3, arg_4, arg_5
    .long {i}
    .long \\battler
    .long \\msg_id
    .long \\tag
    .if \\tag > TAG_NONE
        .long \\arg_0
        .if \\tag > TAG_TRNAME
            .long \\arg_1
            .if \\tag > TAG_TRCLASS_TRNAME
                .long \\arg_2
                .if \\tag > TAG_TRCLASS_TRNAME_ITEM
                    .long \\arg_3
                    .if \\tag > TAG_TRCLASS_TRNAME_TRCLASS_TRNAME
                        .long \\arg_4
                        .long \\arg_5
                    .endif
                .endif
            .endif
        .endif
    .endif
    .endm
"""
        lines.append(currLine)
    elif "CompareVarToValue" in cmd.name:
        currLine = f"""    .macro CompareVarToValue op, var, val, jump
    .long 32
    .long \\op
    .long \\var
    .long \\val
    .long (\\jump-.) / 4 - 1
    .endm
"""
        lines.append(currLine)
    elif "UpdateVarFromVar" in cmd.name:
        currLine = f"""    .macro UpdateVarFromVar op, dst, src
    .long 57
    .long \\op
    .long \\dst
    .long \\src
    .endm
"""
        lines.append(currLine)
    elif "UpdateVar" in cmd.name:
        currLine = f"""    .macro UpdateVar op, var, val
    .long 50
    .long \\op
    .long \\var
    .long \\val
    .endm
"""
        lines.append(currLine)
    elif "DivideVarByValue" in cmd.name:
        currLine = f"""    .macro DivideVarByValue var, val
    .long 85
    .long \\var
    .long \\val
    .endm
"""
        lines.append(currLine)
    elif "CompareMonDataToValue" in cmd.name:
        currLine = f"""    .macro CompareMonDataToValue op, battler, param, val, jump
    .long 33
    .long \\op
    .long \\battler
    .long \\param
    .long \\val
    .long (\\jump-.) / 4 - 1
    .endm
"""
        lines.append(currLine)
    elif "UpdateMonDataFromVar" not in cmd.name and "UpdateMonData" in cmd.name:
        currLine = f"""    .macro UpdateMonData op, battler, param, val
    .long 52
    .long \\op
    .long \\battler
    .long \\param
    .long \\val
    .endm
"""
        lines.append(currLine)
    else:
        if cmd.params:
            lines.append(f'    .macro {cmd.name} {arg_list(cmd.params)}')
        else:
            lines.append(f'    .macro {cmd.name}')
        lines.append(f'    .long {i}')

        for j in range(len(cmd.params)):
            if "Label" in str(cmd.params[j]):
                lines.append(f'    .long (((\\arg_{j} - .) / 4) - {len(cmd.params) - j})')
            else:
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
