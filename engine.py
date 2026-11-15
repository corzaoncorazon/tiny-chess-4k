"""Dev copy of the engine: readable version, before packing to 4 KB."""
import json
import os
import sys
import urllib.request

FILES = "abcdefgh"
VAL = {"p": 100, "n": 325, "b": 335, "r": 500, "q": 975, "k": 0}
PAWN_PST = [0, 0, 0, 0, 0, 0, 0, 0,
            5, 10, 10, -20, -20, 10, 10, 5,
            5, -5, -10, 0, 0, -10, -5, 5,
            0, 0, 0, 20, 20, 0, 0, 0,
            5, 5, 10, 25, 25, 10, 5, 5,
            10, 10, 20, 30, 30, 20, 10, 10,
            50, 50, 50, 50, 50, 50, 50, 50,
            0, 0, 0, 0, 0, 0, 0, 0]
KNIGHT_PST = [-50, -40, -30, -30, -30, -30, -40, -50,
              -40, -20, 0, 5, 5, 0, -20, -40,
              -30, 5, 10, 15, 15, 10, 5, -30,
              -30, 0, 15, 20, 20, 15, 0, -30,
              -30, 5, 15, 20, 20, 15, 5, -30,
              -30, 0, 10, 15, 15, 10, 0, -30,
              -40, -20, 0, 0, 0, 0, -20, -40,
              -50, -40, -30, -30, -30, -30, -40, -50]
BISHOP_PST = [-20, -10, -10, -10, -10, -10, -10, -20,
              -10, 5, 0, 0, 0, 0, 5, -10,
              -10, 10, 10, 10, 10, 10, 10, -10,
              -10, 0, 10, 10, 10, 10, 0, -10,
              -10, 5, 5, 10, 10, 5, 5, -10,
              -10, 0, 5, 10, 10, 5, 0, -10,
              -10, 0, 0, 0, 0, 0, 0, -10,
              -20, -10, -10, -10, -10, -10, -10, -20]
ROOK_PST = [0, 0, 0, 5, 5, 0, 0, 0,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            5, 10, 10, 10, 10, 10, 10, 5,
            0, 0, 0, 0, 0, 0, 0, 0]
QUEEN_PST = [-20, -10, -10, -5, -5, -10, -10, -20,
             -10, 0, 5, 0, 0, 0, 0, -10,
             -10, 5, 5, 5, 5, 5, 0, -10,
             0, 0, 5, 5, 5, 5, 0, -5,
             -5, 0, 5, 5, 5, 5, 0, -5,
             -10, 0, 5, 5, 5, 5, 0, -10,
             -10, 0, 0, 0, 0, 0, 0, -10,
             -20, -10, -10, -5, -5, -10, -10, -20]
KING_PST = [20, 30, 10, 0, 0, 10, 30, 20,
            20, 20, 0, 0, 0, 0, 20, 20,
            -10, -20, -20, -20, -20, -20, -20, -10,
            -20, -30, -30, -40, -40, -30, -30, -20,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30]
PST = {"p": PAWN_PST, "n": KNIGHT_PST, "b": BISHOP_PST, "r": ROOK_PST, "q": QUEEN_PST, "k": KING_PST}
KNIGHT_OFF = (-17, -15, -10, -6, 6, 10, 15, 17)
KING_OFF = (-9, -8, -7, -1, 1, 7, 8, 9)
DIAG = (-9, -7, 7, 9)
ORTH = (-8, -1, 1, 8)


def sqi(name):
    return (int(name[1]) - 1) * 8 + FILES.index(name[0])


def name_of(i):
    return FILES[i % 8] + str(i // 8 + 1)


class Board:
    __slots__ = ("b", "white", "castle", "ep")

    def __init__(self, fen):
        parts = fen.split()
        self.b = [None] * 64
        for r, row in enumerate(parts[0].split("/")):
            f = 0
            for ch in row:
                if ch.isdigit():
                    f += int(ch)
                else:
                    self.b[(7 - r) * 8 + f] = ch
                    f += 1
        self.white = parts[1] == "w"
        self.castle = parts[2] if len(parts) > 2 else "-"
        self.ep = sqi(parts[3]) if len(parts) > 3 and parts[3] != "-" else -1

    def copy(self):
        c = Board.__new__(Board)
        c.b = self.b[:]
        c.white = self.white
        c.castle = self.castle
        c.ep = self.ep
        return c

    def attacked(self, target, by_white):
        b = self.b
        # pawns
        step = -8 if by_white else 8
        for d in (-1, 1):
            i = target + step + d
            if 0 <= i < 64 and abs(i % 8 - (target + step) % 8) == 1:
                p = b[i]
                if p is not None and p.isupper() == by_white and p.lower() == "p":
                    return True
        # knights and king
        for offs, kind in ((KNIGHT_OFF, "n"), (KING_OFF, "k")):
            for d in offs:
                i = target + d
                if not (0 <= i < 64):
                    continue
                if abs(i % 8 - target % 8) > 2:
                    continue
                p = b[i]
                if p is not None and p.isupper() == by_white and p.lower() == kind:
                    return True
        # sliders
        for offs, kinds in ((DIAG, "bq"), (ORTH, "rq")):
            for d in offs:
                i = target + d
                prev = target
                while 0 <= i < 64:
                    if abs(i % 8 - prev % 8) > 1:
                        break
                    p = b[i]
                    if p is not None:
                        if p.isupper() == by_white and p.lower() in kinds:
                            return True
                        break
                    prev = i
                    i += d
        return False

    def king(self, white):
        target = "K" if white else "k"
        for i, p in enumerate(self.b):
            if p == target:
                return i
        return -1

    def legal(self):
        return [m for m in self.pseudo() if self.ok(m)]

    def pseudo(self):
        b = self.b
        out = []
        me = self.white
        for i, p in enumerate(b):
            if p is None or p.isupper() != me:
                continue
            t = p.lower()
            if t == "p":
                step = 8 if me else -8
                start = 1 if me else 6
                promo = 7 if me else 0
                j = i + step
                if 0 <= j < 64 and b[j] is None:
                    out.extend(self.pawn_moves(i, j, promo))
                    k = j + step
                    if i // 8 == start and 0 <= k < 64 and b[k] is None:
                        out.append((i, k, None))
                for d in (-1, 1):
                    j = i + step + d
                    if 0 <= j < 64 and abs(j % 8 - i % 8) == 1:
                        q = b[j]
                        if q is not None and q.isupper() != me:
                            out.extend(self.pawn_moves(i, j, promo))
                        elif j == self.ep and q is None:
                            out.append((i, j, "ep"))
            elif t == "n" or t == "k":
                for d in (KNIGHT_OFF if t == "n" else KING_OFF):
                    j = i + d
                    if not (0 <= j < 64) or abs(j % 8 - i % 8) > 2:
                        continue
                    q = b[j]
                    if q is None or q.isupper() != me:
                        out.append((i, j, None))
            else:
                offs = DIAG if t == "b" else ORTH if t == "r" else DIAG + ORTH
                for d in offs:
                    j = i + d
                    prev = i
                    while 0 <= j < 64 and abs(j % 8 - prev % 8) <= 1:
                        q = b[j]
                        if q is None:
                            out.append((i, j, None))
                        else:
                            if q.isupper() != me:
                                out.append((i, j, None))
                            break
                        prev = j
                        j += d
        # castling
        if me and "K" in self.castle and b[5] is None and b[6] is None:
            if not self.attacked(4, False) and not self.attacked(5, False) and not self.attacked(6, False):
                out.append((4, 6, None))
        if me and "Q" in self.castle and b[3] is None and b[2] is None and b[1] is None:
            if not self.attacked(4, False) and not self.attacked(3, False) and not self.attacked(2, False):
                out.append((4, 2, None))
        if not me and "k" in self.castle and b[61] is None and b[62] is None:
            if not self.attacked(60, True) and not self.attacked(61, True) and not self.attacked(62, True):
                out.append((60, 62, None))
        if not me and "q" in self.castle and b[59] is None and b[58] is None and b[57] is None:
            if not self.attacked(60, True) and not self.attacked(59, True) and not self.attacked(58, True):
                out.append((60, 58, None))
        return out

    def pawn_moves(self, i, j, promo):
        if j // 8 == promo:
            return [(i, j, c) for c in ("q", "r", "b", "n")]
        return [(i, j, None)]

    def ok(self, m):
        c = self.copy()
        c.apply(m)
        return not c.attacked(c.king(self.white), not self.white)

    def apply(self, m):
        i, j, flag = m
        b = self.b
        p = b[i]
        t = p.lower()
        b[i] = None
        if flag == "ep":
            b[j - 8 if p.isupper() else j + 8] = None
        if flag is not None and flag != "ep":
            p = flag.upper() if p.isupper() else flag
        b[j] = p
        if t == "k":
            if i == 4 and self.white:
                self.castle = self.castle.replace("K", "").replace("Q", "")
                if j == 6:
                    b[5], b[7] = b[7], None
                elif j == 2:
                    b[3], b[0] = b[0], None
            elif i == 60 and not self.white:
                self.castle = self.castle.replace("k", "").replace("q", "")
                if j == 62:
                    b[61], b[63] = b[63], None
                elif j == 58:
                    b[59], b[56] = b[56], None
        if t == "r":
            if i == 0:
                self.castle = self.castle.replace("Q", "")
            elif i == 7:
                self.castle = self.castle.replace("K", "")
            elif i == 56:
                self.castle = self.castle.replace("q", "")
            elif i == 63:
                self.castle = self.castle.replace("k", "")
        self.ep = -1
        if t == "p" and abs(j - i) == 16:
            self.ep = (i + j) // 2
        self.white = not self.white

    def eval(self):
        score = 0
        for i, p in enumerate(self.b):
            if p is None:
                continue
            t = p.lower()
            v = VAL[t] + PST[t][i if p.isupper() else 63 - i]
            score += v if p.isupper() else -v
        return score if self.white else -score


def uci(m):
    return name_of(m[0]) + name_of(m[1]) + (m[2] if m[2] and m[2] != "ep" else "")


def search(board, depth, nodes, alpha, beta):
    if nodes[0] <= 0:
        return board.eval()
    nodes[0] -= 1
    if depth <= 0:
        return board.eval()
    moves = board.legal()
    if not moves:
        return -30000 + (10 - depth) if board.attacked(board.king(board.white), not board.white) else 0
    moves.sort(key=lambda m: -VAL[board.b[m[1]].lower()] if board.b[m[1]] else 0)
    best = -32000
    for m in moves:
        c = board.copy()
        c.apply(m)
        v = -search(c, depth - 1, nodes, -beta, -alpha)
        if v > best:
            best = v
        if v > alpha:
            alpha = v
        if alpha >= beta:
            break
    return best


def choose(fen, legal_uci, budget=60000):
    board = Board(fen)
    nodes = [budget]
    scored = []
    for u in legal_uci:
        m = (sqi(u[:2]), sqi(u[2:4]), u[4] if len(u) > 4 else None)
        c = board.copy()
        c.apply(m)
        scored.append((-search(c, 2, nodes, -32000, 32000), u))
    scored.sort()
    return scored[0][1]
