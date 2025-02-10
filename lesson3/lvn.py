import itertools
import json
import sys

TERMINATORS = ("jmp", "br", "ret")

COMMUTATIVE_OPS = ("add", "mul", "eq", "and", "or")

# Map of inequalities to their inverses
INEQUALITIES = {"lt": "ge", "le": "gt", "gt": "le", "ge": "lt"}


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


# First iteration: no folding
# Second iteration: folding


def lvn(instrs):
    names: dict[str, int] = {}
    exprs: dict[tuple, int] = {}
    vns: list[tuple[tuple, str]] = []

    new_instrs = []

    for i, instr in enumerate(instrs):
        # NOTE: Not handling effect operations /"call"s for now
        if "label" in instr or "dest" not in instr or instr["op"] == "call":
            new_instrs.append(instr)
            continue

        op = instr["op"]

        if op == "id":  # Copy propagation
            names[instr["dest"]] = names[instr["args"][0]]
            instr["args"] = vns[names[instr["args"][0]]][1]
            new_instrs.append(instr)
            continue
        if op == "const":
            expr = ("const", instr["value"])
        else:
            argvns = []
            # TODO: Handle unknown values
            for arg in instr["args"]:
                argvs.append(names[arg])
            if op in COMMUTATIVE_OPS:  # Canonize commutative operations
                argvns.sort()
            elif op in INEQUALITIES and argvns[0] > argvns[1]:  # Canonize inequalities
                op = INEQUALITIES[op]
                argvns.reverse()
            expr = (op, *argvns)

        if expr in exprs:
            vn = exprs[expr]
            name = vns[vn][1]
            instr["op"] = "id"
            instr["args"] = [name]

            names[instr["dest"]] = vn
        else:
            names[instr["dest"]] = len(vns)
            exprs[expr] = len(vns)
            vns.append((expr, instr["dest"]))

        new_instrs.append(instr)
    # TODO: Handle renames with blocks :p

    return new_instrs


def lvn0(instrs):
    names: dict[str, int] = {}
    exprs: dict[tuple, int] = {}
    vns: list[tuple[tuple, str]] = []
    uses: dict[str, list[int]] = {}

    new_instrs = []

    # TODO: Keep track of ins that are redefined, re-redefine at end of block...

    # WARN: Do not try to add the result of a function call or other effect instruction as a value!

    for i, instr in enumerate(instrs):
        if "label" in instr:
            new_instrs.append(instr)
            continue

        op = instr["op"]

        if op == "const":
            expr = ("const", instr["value"])
        elif "args" in instr:
            argvs = []
            for arg in instr.get("args", []):
                if arg not in names:  # Unknown value
                    names[arg] = len(vns)
                    vns.append((None, arg))
                    argvs.append(arg)
                else:
                    argvs.append(names[arg])
            if op in COMMUTATIVE_OPS:  # Canonicalize commutative operations
                argvs.sort()
            if op in INEQUALITIES and argvs[0] > argvs[1]:  # Canonicalize inequalities
                op = INEQUALITIES[op]
                argvs.reverse()
            expr = (op, *argvs)

        # TODO: For non-effect instructions... add dest to values (?)

        if "dest" in instr and instr["op"] != "call":
            if expr in exprs:
                vn = exprs[expr]
                name = vns[vn][1]
                instr = {"op": "id", "args": [name]}
                instr["op"] = "id"
                instr["args"] = [name]

                new_instrs.append(instr)
                uses[name].append(i)
                names[instr["dest"]] = vn
            else:
                instr["args"] = [vns[vn][1] for vn in argvs]
                # ...?
        else:
            pass

        # Translation step for converting instruction?

        # Patch in uses around here?

        new_instrs.append(instr)

    # TODO: Return new block
