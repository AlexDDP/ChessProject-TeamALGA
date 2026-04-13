"""
team_alpha.py  —  Chess Bot using Minimax + Alpha-Beta Pruning
Heuristic: Material value

Install dependency:  pip install python-chess
"""

import chess
import chess.polyglot

# ── Piece values (centipawns) ─────────────────────────────────────────────────
# Standard values adjusted based on modern engine research:
#   - Knight dropped slightly — weaker in open positions
#   - Queen bumped slightly — reflects her true dominance
#   - Bishop pair bonus added separately below
PIECE_VALUES = {
    chess.PAWN:   100,
    chess.KNIGHT: 310,   # slightly weaker than bishop in open games
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  950,   # slightly stronger than 9 pawns
    chess.KING:   20000,
}

# Having both bishops together is worth roughly half a pawn extra
BISHOP_PAIR_BONUS = 50

# Piece-Square Tables — bonus points based on WHERE a piece is on the board
# Positive = good square, Negative = bad square
# These are from White's perspective; Black's tables are mirrored automatically

PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

PST = {
    chess.PAWN:   PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK:   ROOK_TABLE,
    chess.QUEEN:  QUEEN_TABLE,
    chess.KING:   KING_TABLE,
}

# ── Transposition Table ───────────────────────────────────────────────────────
# Caches positions we have already searched so we never re-evaluate the same
# board state twice.  chess.polyglot.zobrist_hash(board) produces a unique 64-bit key
# for every distinct position.
#
# Each entry stores:
#   'depth'  — how deeply we searched from this node
#   'flag'   — what the stored value represents (see flag types below)
#   'value'  — the score we found
#
# Flag types:
#   TT_EXACT — value is the true minimax score (we searched the full window)
#   TT_LOWER — we got a beta cutoff; real value is >= stored value (lower bound)
#   TT_UPPER — we never raised alpha; real value is <= stored value (upper bound)

TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2

transposition_table: dict = {}


# ── Heuristic ─────────────────────────────────────────────────────────────────
def evaluate(board: chess.Board) -> float:
    """
    Comprehensive static evaluation function.
    Score > 0 => White is better.
    Score < 0 => Black is better.
    """
    # ── Terminal / draw states ────────────────────────────────────────────
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    if board.is_repetition(3) or board.is_fifty_moves():
        return 0

    score = 0

    # ── Game phase detection ──────────────────────────────────────────────
    # Endgame = both queens gone or very little material left.
    # Passed pawns and king activity become much more important in endgames.
    queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + \
             len(board.pieces(chess.QUEEN, chess.BLACK))
    endgame = (queens == 0)

    # ── 1. MATERIAL + PIECE-SQUARE TABLES ────────────────────────────────
    # Count material and positional bonuses in a single pass over the board.
    white_bishops = 0
    black_bishops = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue

        if piece.piece_type == chess.BISHOP:
            if piece.color == chess.WHITE:
                white_bishops += 1
            else:
                black_bishops += 1

        if piece.color == chess.WHITE:
            pst_index = 63 - square
            score += PIECE_VALUES[piece.piece_type]
            score += PST[piece.piece_type][pst_index]
        else:
            pst_index = square
            score -= PIECE_VALUES[piece.piece_type]
            score -= PST[piece.piece_type][pst_index]

    # ── 2. BISHOP PAIR BONUS ──────────────────────────────────────────────
    # Two bishops cover both square colours and dominate open positions.
    # Worth roughly half a pawn extra over a bishop + knight.
    if white_bishops >= 2:
        score += BISHOP_PAIR_BONUS
    if black_bishops >= 2:
        score -= BISHOP_PAIR_BONUS

    # ── 3. MOBILITY ───────────────────────────────────────────────────────
    # More legal moves = more options = better position.
    # We temporarily pass the turn to count the other side's moves.
    if board.turn == chess.WHITE:
        white_mobility = len(list(board.legal_moves))
        board.push(chess.Move.null())
        black_mobility = len(list(board.legal_moves))
        board.pop()
    else:
        black_mobility = len(list(board.legal_moves))
        board.push(chess.Move.null())
        white_mobility = len(list(board.legal_moves))
        board.pop()

    score += 0.1 * (white_mobility - black_mobility)

    # ── 4. KING SAFETY ────────────────────────────────────────────────────
    # Three layers: castling status, pawn shield, open file near king.
    # In the endgame we skip this — kings should be active, not hiding.
    if not endgame:
        for color, sign in [(chess.WHITE, 1), (chess.BLACK, -1)]:
            king_sq   = board.king(color)
            king_file = chess.square_file(king_sq)
            king_rank = chess.square_rank(king_sq)

            # Layer 1: castling status
            # Reward actually castling (+60), reward having the option (+20),
            # penalise losing rights without castling (-40).
            castled = (
                (color == chess.WHITE and king_sq in (chess.G1, chess.C1)) or
                (color == chess.BLACK and king_sq in (chess.G8, chess.C8))
            )
            if castled:
                score += sign * 60
            elif board.has_castling_rights(color):
                score += sign * 20
            else:
                if king_sq in (chess.E1, chess.E8):
                    score -= sign * 40   # stuck in the centre

            # Layer 2: pawn shield
            # Each pawn directly in front of the king adds +18.
            shield_rank = king_rank + (1 if color == chess.WHITE else -1)
            if 0 <= shield_rank <= 7:
                for df in (-1, 0, 1):
                    f = king_file + df
                    if 0 <= f <= 7:
                        p = board.piece_at(chess.square(f, shield_rank))
                        if p and p.piece_type == chess.PAWN and p.color == color:
                            score += sign * 18

            # Layer 3: open file toward the king
            # No friendly pawn on the king's file = highway for enemy rooks/queens.
            friendly_pawn_on_file = any(
                board.piece_at(chess.square(king_file, r)) is not None
                and board.piece_at(chess.square(king_file, r)).piece_type == chess.PAWN
                and board.piece_at(chess.square(king_file, r)).color == color
                for r in range(8)
            )
            if not friendly_pawn_on_file:
                score -= sign * 35

    # ── 5. CHECK BONUS ────────────────────────────────────────────────────
    if board.is_check():
        score += 20 if board.turn == chess.BLACK else -20

    # ── 6. PAWN STRUCTURE ─────────────────────────────────────────────────
    # Analyse every pawn on the board for structural weaknesses and strengths.
    #
    # Doubled pawns (-20): two friendly pawns on the same file.  They block
    #   each other, can't defend each other, and are easy targets.
    #
    # Isolated pawns (-25): no friendly pawns on adjacent files.  The pawn
    #   can never be defended by another pawn and requires piece support.
    #
    # Passed pawns (+bonus): no enemy pawns can ever block or capture it on
    #   its path to promotion.  The bonus scales with how far advanced the
    #   pawn is, and doubles in the endgame where passed pawns are decisive.
    #
    # Pawn chains (+10): a pawn defended diagonally by a friendly pawn.
    #   Interlocked chains are very hard to break and control space.

    for color, sign in [(chess.WHITE, 1), (chess.BLACK, -1)]:
        enemy = not color
        pawns = board.pieces(chess.PAWN, color)
        pawn_files = [chess.square_file(sq) for sq in pawns]

        for sq in pawns:
            f = chess.square_file(sq)
            r = chess.square_rank(sq)

            # Doubled pawns
            if pawn_files.count(f) > 1:
                score -= sign * 20

            # Isolated pawns
            neighbors = [af for af in (f - 1, f + 1) if 0 <= af <= 7]
            if not any(af in pawn_files for af in neighbors):
                score -= sign * 25

            # Passed pawns — no enemy pawn on same or adjacent files ahead
            ahead = range(r + 1, 8) if color == chess.WHITE else range(r - 1, -1, -1)
            passed = True
            for ar in ahead:
                for af in [f - 1, f, f + 1]:
                    if 0 <= af <= 7:
                        blocker = board.piece_at(chess.square(af, ar))
                        if blocker and blocker.piece_type == chess.PAWN \
                                and blocker.color == enemy:
                            passed = False
                            break
                if not passed:
                    break

            if passed:
                # Bonus scales with advancement (rank 1 = 45, rank 6 = 120)
                advance  = r if color == chess.WHITE else (7 - r)
                bonus    = 30 + 15 * advance
                if endgame:
                    bonus *= 2   # passed pawns win endgames
                score += sign * bonus

            # Pawn chains — defended diagonally by a friendly pawn behind
            back_rank = r - 1 if color == chess.WHITE else r + 1
            if 0 <= back_rank <= 7:
                for df in (-1, 1):
                    bf = f + df
                    if 0 <= bf <= 7:
                        support = board.piece_at(chess.square(bf, back_rank))
                        if support and support.piece_type == chess.PAWN \
                                and support.color == color:
                            score += sign * 10

    # ── 7. ROOKS ON OPEN / SEMI-OPEN FILES ───────────────────────────────
    # Open file (no pawns at all): rook has full mobility → +50
    # Semi-open file (no friendly pawns): rook can pressure enemy → +25
    # Rooks need open lines to be effective; a rook locked behind its own
    # pawns is worth far less than its material value suggests.
    for color, sign in [(chess.WHITE, 1), (chess.BLACK, -1)]:
        for rook_sq in board.pieces(chess.ROOK, color):
            f = chess.square_file(rook_sq)
            friendly_pawn = any(
                board.piece_at(chess.square(f, r)) is not None
                and board.piece_at(chess.square(f, r)).piece_type == chess.PAWN
                and board.piece_at(chess.square(f, r)).color == color
                for r in range(8)
            )
            enemy_pawn = any(
                board.piece_at(chess.square(f, r)) is not None
                and board.piece_at(chess.square(f, r)).piece_type == chess.PAWN
                and board.piece_at(chess.square(f, r)).color != color
                for r in range(8)
            )
            if not friendly_pawn and not enemy_pawn:
                score += sign * 50   # fully open file
            elif not friendly_pawn:
                score += sign * 25   # semi-open file

    # ── 8. CONNECTED ROOKS ────────────────────────────────────────────────
    # Two rooks on the same rank or file with no pieces between them are
    # "connected" — they protect each other and double their attacking power.
    # A connected rook pair is one of the strongest middlegame structures.
    for color, sign in [(chess.WHITE, 1), (chess.BLACK, -1)]:
        rooks = list(board.pieces(chess.ROOK, color))
        if len(rooks) >= 2:
            r1, r2 = rooks[0], rooks[1]
            same_rank = chess.square_rank(r1) == chess.square_rank(r2)
            same_file = chess.square_file(r1) == chess.square_file(r2)
            if same_rank or same_file:
                between = chess.SquareSet(chess.between(r1, r2))
                if all(board.piece_at(sq) is None for sq in between):
                    score += sign * 40

    # ── 9. HANGING PIECES ─────────────────────────────────────────────────
    # A piece is "hanging" if it is attacked by the opponent but not defended
    # by any friendly piece.  Leaving pieces hanging is a tactical blunder —
    # we penalise it heavily (90% of the piece's value) to teach the bot to
    # keep its pieces protected and to exploit the opponent's loose pieces.
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None or piece.piece_type == chess.KING:
            continue

        attacked_by_white = len(board.attackers(chess.WHITE, square)) > 0
        attacked_by_black = len(board.attackers(chess.BLACK, square)) > 0

        if piece.color == chess.WHITE and attacked_by_black and not attacked_by_white:
            score -= int(0.9 * PIECE_VALUES[piece.piece_type])
        elif piece.color == chess.BLACK and attacked_by_white and not attacked_by_black:
            score += int(0.9 * PIECE_VALUES[piece.piece_type])

    # ── 10. BISHOP OPEN DIAGONALS ─────────────────────────────────────────
    # board.attacks(sq) returns every square the bishop can currently see.
    # A bishop with 10+ visible squares is on an open diagonal and extremely
    # active; one with 3 squares is locked behind pawns and nearly useless.
    # We award 3 centipawns per visible square to reflect this difference.
    for color, sign in [(chess.WHITE, 1), (chess.BLACK, -1)]:
        for bishop_sq in board.pieces(chess.BISHOP, color):
            vision = len(board.attacks(bishop_sq))
            score += sign * 3 * vision

    # ── 11. CENTRE CONTROL ────────────────────────────────────────────────
    # The four central squares (d4, d5, e4, e5) are the most strategically
    # important on the board — pieces placed here influence both sides and
    # restrict the opponent's piece activity.
    # We reward two things:
    #   - Physically occupying a centre square with any piece (+15)
    #   - Attacking a centre square (+5 per attacker)
    for sq in (chess.D4, chess.D5, chess.E4, chess.E5):
        piece = board.piece_at(sq)
        if piece:
            score += 15 if piece.color == chess.WHITE else -15

        white_attackers = len(board.attackers(chess.WHITE, sq))
        black_attackers = len(board.attackers(chess.BLACK, sq))
        score += 5 * white_attackers
        score -= 5 * black_attackers

    return score


# ── Move ordering ─────────────────────────────────────────────────────────────
def _order_moves(board: chess.Board) -> list:
    """
    Sort moves best-first so alpha-beta finds cutoffs as early as possible.

    Priority (highest first):
      1. TT move — the best move stored from a previous search of this position.
         Searching it first almost always produces an immediate cutoff.
      2. Captures scored by MVV-LVA (Most Valuable Victim - Least Valuable
         Attacker).  Capturing a queen with a pawn scores highest; capturing a
         pawn with a queen scores lowest.  Good captures get searched before
         quiet moves, producing cutoffs that prune the quiet subtree entirely.
      3. Promotions — a pawn promoting to a queen is extremely valuable.
      4. Quiet moves last — no special ordering among these yet.

    Why MVV-LVA?
      Alpha-beta prunes a branch the moment it finds a move better than what
      the opponent would allow.  Searching a winning capture first tightens
      the bound immediately and skips all remaining (worse) moves.  Random
      capture order wastes time finding the good one late.
    """
    tt_move = None
    tt_entry = transposition_table.get(chess.polyglot.zobrist_hash(board))
    if tt_entry is not None:
        tt_move = tt_entry.get('best_move')

    def move_score(move: chess.Move) -> int:
        if move == tt_move:
            return 30000                          # TT move always first

        score = 0

        if move.promotion:
            score += 20000 + PIECE_VALUES.get(move.promotion, 0)

        if board.is_capture(move):
            victim   = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            victim_val   = PIECE_VALUES.get(victim.piece_type,   0) if victim   else 0
            attacker_val = PIECE_VALUES.get(attacker.piece_type, 0) if attacker else 0
            score += 10000 + victim_val - attacker_val   # MVV-LVA

        return score

    moves = list(board.legal_moves)
    moves.sort(key=move_score, reverse=True)
    return moves


# ── Quiescence Search ────────────────────────────────────────────────────────
def quiescence(board: chess.Board, alpha: float, beta: float,
               qdepth: int = 4) -> float:
    """
    Extend the search beyond depth 0 by looking at captures only, until the
    position is 'quiet' (no captures left) or qdepth is exhausted.

    qdepth limits how many capture plies we look ahead — without it,
    a long capture chain in a complex middlegame can recurse 10+ levels deep
    and make each move take seconds.  4 plies covers virtually all real
    capture sequences (take, retake, take, retake) while keeping it fast.
    """
    stand_pat = evaluate(board)

    # Beta cutoff — position already too good; opponent wouldn't allow this
    if stand_pat >= beta:
        return beta

    # Update alpha — we can always stand pat instead of capturing
    if stand_pat > alpha:
        alpha = stand_pat

    # Hard limit — stop extending if we've gone deep enough into captures
    if qdepth == 0:
        return alpha

    # Try every capture, sorted MVV-LVA best-first
    captures = [m for m in board.legal_moves if board.is_capture(m)]
    captures.sort(
        key=lambda m: (
            PIECE_VALUES.get(board.piece_at(m.to_square).piece_type, 0)
            if board.piece_at(m.to_square) else 0
        ) - (
            PIECE_VALUES.get(board.piece_at(m.from_square).piece_type, 0)
            if board.piece_at(m.from_square) else 0
        ),
        reverse=True
    )

    for move in captures:
        board.push(move)
        score = -quiescence(board, -beta, -alpha, qdepth - 1)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


# ── Minimax with Alpha-Beta Pruning + Transposition Table + Move Ordering ──────
def minimax(board: chess.Board, depth: int,
            alpha: float, beta: float,
            maximizing: bool) -> float:
    """
    Minimax with Alpha-Beta cutoffs, transposition table, and move ordering.

    Before searching, we check if this exact position has already been seen
    at equal or greater depth.  If so, we reuse the stored result instead of
    re-searching the whole subtree.

    Moves are ordered best-first via _order_moves() so alpha-beta prunes as
    early as possible.  The best move found is stored back into the TT entry
    so the next search of this position uses it as the first move tried.
    """
    alpha_orig = alpha

    # ── Transposition table lookup ────────────────────────────────────────
    key = chess.polyglot.zobrist_hash(board)
    tt_entry = transposition_table.get(key)

    if tt_entry is not None and tt_entry['depth'] >= depth:
        tt_val  = tt_entry['value']
        tt_flag = tt_entry['flag']

        if tt_flag == TT_EXACT:
            return tt_val
        elif tt_flag == TT_LOWER:
            alpha = max(alpha, tt_val)
        elif tt_flag == TT_UPPER:
            beta  = min(beta,  tt_val)

        if alpha >= beta:
            return tt_val

    # ── Base cases ────────────────────────────────────────────────────────
    if board.is_game_over():
        return evaluate(board)

    if depth == 0:
        # Drop into quiescence search instead of evaluating immediately.
        # This eliminates the horizon effect — we keep searching captures
        # until the position is genuinely quiet before scoring it.
        return quiescence(board, alpha, beta)

    # ── Search ────────────────────────────────────────────────────────────
    best_move_found = None

    if maximizing:
        best = float('-inf')
        for move in _order_moves(board):
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if score > best:
                best = score
                best_move_found = move
            alpha = max(alpha, best)
            if beta <= alpha:
                break       # Beta cutoff — prune remaining moves
    else:
        best = float('inf')
        for move in _order_moves(board):
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if score < best:
                best = score
                best_move_found = move
            beta = min(beta, best)
            if beta <= alpha:
                break       # Alpha cutoff — prune remaining moves

    # ── Store result ──────────────────────────────────────────────────────
    if best <= alpha_orig:
        flag = TT_UPPER
    elif best >= beta:
        flag = TT_LOWER
    else:
        flag = TT_EXACT

    transposition_table[key] = {
        'depth':     depth,
        'flag':      flag,
        'value':     best,
        'best_move': best_move_found,  # used by _order_moves() on the next visit
    }

    return best


# ── Entry point called by the tournament harness ──────────────────────────────
def get_next_move(board: chess.Board,
                  color: chess.Color,
                  depth: int = 3) -> chess.Move:
    """
    Return the best move for `color` from the current `board` position.
    Uses Iterative Deepening: searches depth 1, 2, 3, ... up to `depth`.

    Why iterative deepening?
      - Each shallow search fills the transposition table with good scores.
      - When the next deeper search hits those TT entries, it immediately has
        tighter alpha/beta bounds, so alpha-beta prunes far more branches.
      - The total extra work of the shallower passes is small (depth 1+2 cost
        almost nothing compared to depth 3), but the pruning benefit is large.
      - We always have a valid best_move from the previous iteration, so if
        something were to cut the search short we still return a legal move.

    DO NOT rename or change this signature — the harness calls it directly.
    """
    # Keep the TT across iterations within the same move search — this is the
    # whole point of iterative deepening.  Clear it only between moves so
    # stale entries from the previous turn don't pollute this search.
    transposition_table.clear()

    maximizing = (color == chess.WHITE)
    best_move  = None

    # Search depth 1, 2, 3, ..., depth
    # Each pass refines best_move and populates the TT for the next pass
    for current_depth in range(1, depth + 1):
        best_score = float('-inf') if maximizing else float('inf')
        current_best_move = None

        b = board.copy()   # never modify the board passed in

        # Order the moves using the previous iteration's TT scores so the
        # best candidate is searched first — maximising early cutoffs
        moves = list(b.legal_moves)
        moves.sort(
            key=lambda m: _tt_move_score(b, m, maximizing),
            reverse=True
        )

        for move in moves:
            b.push(move)
            score = minimax(b, current_depth - 1,
                            float('-inf'), float('inf'),
                            not maximizing)
            b.pop()

            if maximizing and score > best_score:
                best_score, current_best_move = score, move
            elif not maximizing and score < best_score:
                best_score, current_best_move = score, move

        if current_best_move is not None:
            best_move = current_best_move   # commit the result of this iteration

    return best_move


def _tt_move_score(board: chess.Board, move: chess.Move, maximizing: bool) -> float:
    """
    Score a move for root-level ordering using the transposition table.
    After a shallower iteration, the TT already holds scores for positions
    one move deep — we use those to sort the root moves best-first for the
    next iteration, so alpha-beta sees good moves early and prunes more.
    """
    board.push(move)
    key = chess.polyglot.zobrist_hash(board)
    board.pop()

    entry = transposition_table.get(key)
    if entry is None:
        return 0  # no info yet — treat as neutral

    # Return score from White's perspective for consistent sorting
    return entry['value'] if maximizing else -entry['value']


# ── Quick self-test ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    b = chess.Board()
    move = get_next_move(b, chess.WHITE, depth=3)
    print(f"[team_alpha] Opening move: {b.san(move)}")