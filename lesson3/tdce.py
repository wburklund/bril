import itertools
import json
import sys

TERMINATORS = ("jmp", "br", "ret")


def form_blocks(body):
    blocks = []
    cur_block = []

    for instr in body:
        if "op" in instr:  # An actual instruction.
            cur_block.append(instr)

            # Check for terminator.
            if instr["op"] in TERMINATORS:
                blocks.append(cur_block)
                cur_block = []
        else:  # A label.
            if len(cur_block) > 0:
                blocks.append(cur_block)
            cur_block = [instr]

    if len(cur_block) > 0:
        blocks.append(cur_block)

    return blocks


def tdce_pass(instrs):
    changed = False

    used = set()
    for instr in instrs:
        used.update(instr.get("args", []))

    for i in reversed(range(len(instrs))):
        instr = instrs[i]
        if "dest" in instr and instr["dest"] not in used:
            instrs.pop(i)
            changed = True

    return changed


def tdce():
    prog = json.load(sys.stdin)

    for func in prog["functions"]:
        while tdce_pass(func["instrs"]):
            pass

        blocks = form_blocks(func["instrs"])
        for block in blocks:
            unused = {}
            to_remove = []
            for i, instr in enumerate(block):
                for arg in instr.get("args", []):
                    unused.pop(arg, None)
                if "dest" in instr:
                    dest = instr["dest"]
                    if dest in unused:
                        to_remove.append(unused[dest])
                    unused[dest] = i
            for i in reversed(to_remove):
                block.pop(i)

        func["instrs"] = list(itertools.chain(*blocks))

    print(json.dumps(prog))


if __name__ == "__main__":
    tdce()
