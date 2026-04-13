"""
team_alpha.py  —  Chess Bot using Minimax + Alpha-Beta Pruning
Heuristic: Stockfish-inspired evaluation

Install dependency:  pip install python-chess
"""

import chess

# ── Piece values (centipawns) ─────────────────────────────────────────────────
PIECE_VALUES = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  900,
    chess.KING:   20000,
}

# ── Piece-Square Tables (Stockfish-inspired) ──────────────────────────────────
# These tables give bonuses for pieces on good squares
# Values are from White's perspective (need to flip for Black)

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
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
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

KING_MIDDLE_GAME_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

KING_END_GAME_TABLE = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

# ── Helper Functions ──────────────────────────────────────────────────────────

def get_piece_square_value(piece_type: int, square: int, color: chess.Color, is_endgame: bool) -> int:
    """Get the piece-square table value for a piece."""
    # Map piece type to table
    if piece_type == chess.PAWN:
        table = PAWN_TABLE
    elif piece_type == chess.KNIGHT:
        table = KNIGHT_TABLE
    elif piece_type == chess.BISHOP:
        table = BISHOP_TABLE
    elif piece_type == chess.ROOK:
        table = ROOK_TABLE
    elif piece_type == chess.QUEEN:
        table = QUEEN_TABLE
    elif piece_type == chess.KING:
        table = KING_END_GAME_TABLE if is_endgame else KING_MIDDLE_GAME_TABLE
    else:
        return 0

    # For black pieces, flip the square vertically
    if color == chess.BLACK:
        square = square ^ 56  # Flip rank

    return table[square]


def is_endgame(board: chess.Board) -> bool:
    """
    Determine if we're in the endgame.
    Simple heuristic: endgame if queens are off or total material is low.
    """
    # No queens on the board
    if not board.pieces(chess.QUEEN, chess.WHITE) and not board.pieces(chess.QUEEN, chess.BLACK):
        return True

    # Count non-pawn, non-king pieces
    white_minors = len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.WHITE))
    white_rooks = len(board.pieces(chess.ROOK, chess.WHITE))
    black_minors = len(board.pieces(chess.KNIGHT, chess.BLACK)) + len(board.pieces(chess.BISHOP, chess.BLACK))
    black_rooks = len(board.pieces(chess.ROOK, chess.BLACK))

    # Endgame if both sides have limited material
    return (white_minors + white_rooks <= 2) and (black_minors + black_rooks <= 2)


def evaluate_mobility(board: chess.Board) -> int:
    """
    Mobility: count legal moves (more moves = better position).
    This rewards active pieces and punishes cramped positions.
    """
    # Count moves for current side
    current_mobility = board.legal_moves.count()

    # Switch sides and count opponent's moves
    board.push(chess.Move.null())
    opponent_mobility = board.legal_moves.count()
    board.pop()

    # Return difference (from White's perspective)
    if board.turn == chess.WHITE:
        return (current_mobility - opponent_mobility) * 10
    else:
        return (opponent_mobility - current_mobility) * 10


def evaluate_pawn_structure(board: chess.Board) -> int:
    """
    Evaluate pawn structure:
    - Penalize doubled pawns
    - Penalize isolated pawns
    - Reward passed pawns
    """
    score = 0

    for color in [chess.WHITE, chess.BLACK]:
        multiplier = 1 if color == chess.WHITE else -1
        pawns = board.pieces(chess.PAWN, color)

        for square in pawns:
            file = chess.square_file(square)
            rank = chess.square_rank(square)

            # Check for doubled pawns
            pawns_on_file = [s for s in pawns if chess.square_file(s) == file]
            if len(pawns_on_file) > 1:
                score -= 10 * multiplier

            # Check for isolated pawns (no friendly pawns on adjacent files)
            has_neighbor = False
            for adj_file in [file - 1, file + 1]:
                if 0 <= adj_file <= 7:
                    if any(chess.square_file(s) == adj_file for s in pawns):
                        has_neighbor = True
                        break

            if not has_neighbor:
                score -= 15 * multiplier

            # Check for passed pawns (no enemy pawns blocking or controlling)
            is_passed = True
            if color == chess.WHITE:
                blocking_ranks = range(rank + 1, 8)
            else:
                blocking_ranks = range(0, rank)

            enemy_pawns = board.pieces(chess.PAWN, not color)
            for check_file in [file - 1, file, file + 1]:
                if 0 <= check_file <= 7:
                    for check_rank in blocking_ranks:
                        check_square = chess.square(check_file, check_rank)
                        if check_square in enemy_pawns:
                            is_passed = False
                            break
                if not is_passed:
                    break

            if is_passed:
                # Reward based on how advanced the pawn is
                advancement = rank if color == chess.WHITE else (7 - rank)
                score += (20 + advancement * 10) * multiplier

    return score


def evaluate_king_safety(board: chess.Board, is_endgame_phase: bool) -> int:
    """
    Evaluate king safety in middle game.
    In endgame, centralized king is good (handled by piece-square tables).
    """
    if is_endgame_phase:
        return 0

    score = 0

    for color in [chess.WHITE, chess.BLACK]:
        multiplier = 1 if color == chess.WHITE else -1
        king_square = board.king(color)

        if king_square is None:
            continue

        # Reward castling
        if color == chess.WHITE:
            if king_square in [chess.G1, chess.C1]:  # Castled position
                score += 30 * multiplier
        else:
            if king_square in [chess.G8, chess.C8]:  # Castled position
                score += 30 * multiplier

        # Count pawn shield
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)

        shield_count = 0
        for file_offset in [-1, 0, 1]:
            shield_file = king_file + file_offset
            if 0 <= shield_file <= 7:
                shield_rank = king_rank + (1 if color == chess.WHITE else -1)
                if 0 <= shield_rank <= 7:
                    shield_square = chess.square(shield_file, shield_rank)
                    if board.piece_at(shield_square) == chess.Piece(chess.PAWN, color):
                        shield_count += 1

        score += shield_count * 10 * multiplier

    return score


# ── Heuristic ─────────────────────────────────────────────────────────────────
def evaluate(board: chess.Board) -> float:
    """
    Stockfish-inspired evaluation function combining:
    1. Material value
    2. Piece-square tables (positional value)
    3. Mobility (number of legal moves)
    4. Pawn structure (doubled, isolated, passed pawns)
    5. King safety (castling, pawn shield)

    Score > 0  =>  White is better.
    Score < 0  =>  Black is better.
    """
    # Terminal positions
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    # Determine game phase
    endgame = is_endgame(board)

    score = 0

    # 1. Material + Piece-Square Tables
    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
        # White pieces
        for square in board.pieces(piece_type, chess.WHITE):
            score += PIECE_VALUES[piece_type]
            score += get_piece_square_value(piece_type, square, chess.WHITE, endgame)

        # Black pieces
        for square in board.pieces(piece_type, chess.BLACK):
            score -= PIECE_VALUES[piece_type]
            score -= get_piece_square_value(piece_type, square, chess.BLACK, endgame)

    # 2. Mobility (encourages active piece play)
    score += evaluate_mobility(board)

    # 3. Pawn structure
    score += evaluate_pawn_structure(board)

    # 4. King safety (middle game only)
    score += evaluate_king_safety(board, endgame)

    # 5. Bishop pair bonus
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        score += 30
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        score -= 30

    return score


# ── Minimax with Alpha-Beta Pruning ───────────────────────────────────────────
def minimax(board: chess.Board, depth: int,
            alpha: float, beta: float,
            maximizing: bool) -> float:
    """
    Standard Minimax search with Alpha-Beta cutoffs.
    maximizing=True means we are searching for the best move for White.
    """
    if depth == 0 or board.is_game_over():
        return evaluate(board)

    if maximizing:
        best = float('-inf')
        for move in board.legal_moves:
            board.push(move)
            best = max(best, minimax(board, depth - 1, alpha, beta, False))
            board.pop()
            alpha = max(alpha, best)
            if beta <= alpha:
                break       # Beta cutoff — opponent won't allow this path
        return best
    else:
        best = float('inf')
        for move in board.legal_moves:
            board.push(move)
            best = min(best, minimax(board, depth - 1, alpha, beta, True))
            board.pop()
            beta = min(beta, best)
            if beta <= alpha:
                break       # Alpha cutoff
        return best


# ── Entry point called by the tournament harness ──────────────────────────────
def get_next_move(board: chess.Board,
                  color: chess.Color,
                  depth: int = 3) -> chess.Move:
    """
    Return the best move for `color` from the current `board` position.
    DO NOT rename or change this signature — the harness calls it directly.
    """
    best_move  = None
    maximizing = (color == chess.WHITE)
    best_score = float('-inf') if maximizing else float('inf')

    b = board.copy()   # never modify the board passed in
    for move in b.legal_moves:
        b.push(move)
        score = minimax(b, depth - 1,
                        float('-inf'), float('inf'),
                        not maximizing)
        b.pop()

        if maximizing and score > best_score:
            best_score, best_move = score, move
        elif not maximizing and score < best_score:
            best_score, best_move = score, move

    return best_move


# ── Quick self-test ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    b = chess.Board()
    move = get_next_move(b, chess.WHITE, depth=3)
    print(f"[team_alpha] Opening move: {b.san(move)}")