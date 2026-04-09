"""
team_ALGA_sample.py  —  Chess Bot using Minimax + Alpha-Beta Pruning
Heuristic: Combination of piece values , king safety ,  center control , castling bonuses and piece safety heuristics

"""

import chess


# ── Piece values (centipawns) ─────────────────────────────────────────────────
PIECE_VALUES = {
    chess.PAWN: 10,chess.KNIGHT: 20, chess.BISHOP: 20,
    chess.ROOK:50, chess.QUEEN:  90, chess.KING:   200,
}


# Bonuses for pieces attacking the center
ATTACKING_BONUS = {
    chess.PAWN: 1.5, chess.KNIGHT: 3.0, chess.BISHOP: 2.5,
    chess.ROOK: 1.5, chess.QUEEN: 1.0,  chess.KING: 0.5,
}

# Bonuses for the piece occupying the central sqaures
OCCUPANCY_BONUS = {
    chess.PAWN: 8.0, chess.KNIGHT: 10.0, chess.BISHOP: 7.0,
    chess.ROOK: 5.0, chess.QUEEN: 3.0,   chess.KING: 0.0,
}

# Reduces move repitition
def mobility(board):
    return len(list(board.legal_moves))


def material(board):
    score = 0
    for piece_type, value in PIECE_VALUES.map():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value
    return score


def king_safety(board):
    score = 0

    for color in [chess.WHITE, chess.BLACK]:
        king_sq = board.king(color)
        if king_sq is None:
            continue

        pawn_shield = 0
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece and piece.piece_type == chess.PAWN and piece.color == color:
                if chess.square_distance(sq, king_sq) <= 2:
                    pawn_shield += 1

        if color == chess.WHITE:
            score += pawn_shield * 5
        else:
            score -= pawn_shield * 5

    return score


def control_center(board: chess.Board) -> float:

    # Defining central squares
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]

    score = 0.0


    for square in center_squares:

        # Gets the piece at the current center square
        piece = board.piece_at(square)

        if piece is not None:
            # Gives bonus for occupying center
            if piece.color == chess.WHITE:
                score += OCCUPANCY_BONUS[piece.piece_type]
            else:
                score -= OCCUPANCY_BONUS[piece.piece_type]


        # Gives bonus for pieces attacking center

        for attacker_color, sign in ((chess.WHITE, 1), (chess.BLACK, -1)):
            for attacker_sq in board.attackers(attacker_color, square):
                attacker = board.piece_at(attacker_sq)
                if attacker:
                    score += sign * ATTACKING_BONUS[attacker.piece_type]

    return score


def piece_safety(board):
    score = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue

        attackers = board.attackers(not piece.color, square)
        defenders = board.attackers(piece.color, square)

        if len(attackers) > len(defenders):
            penalty = PIECE_VALUES[piece.piece_type] * 0.3

            if piece.color == chess.WHITE:
                score -= penalty
            else:
                score += penalty

    return score


def hanging_pieces(board):
    score = 0

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None or piece.piece_type == chess.KING:
            continue

        attackers = board.attackers(not piece.color, square)
        defenders = board.attackers(piece.color, square)

        if attackers and not defenders:
            penalty = PIECE_VALUES[piece.piece_type] * 0.6

            if piece.color == chess.WHITE:
                score -= penalty
            else:
                score += penalty

    return score


def castling_bonus(board):
    score = 0

    if board.king(chess.WHITE) in [chess.G1, chess.C1]:
        score += 30
    if board.king(chess.BLACK) in [chess.G8, chess.C8]:
        score -= 30

    return score


# ── Heuristic ─────────────────────────────────────────────────────────────────
def evaluate(board: chess.Board):

    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999

    if (board.is_stalemate() or board.is_insufficient_material() or
        board.is_repetition(3) or board.is_fifty_moves()):
        return 0

    score = 0

    
    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

  
    score += 0.7 * control_center(board)
    score += 1.2 * hanging_pieces(board)
    score += 0.5 * king_safety(board)
    score += 0.4 * castling_bonus(board)
    score += 0.5 * piece_safety(board)

    
    mobility_score = len(list(board.legal_moves))
    if board.turn == chess.WHITE:
        score += 0.15 * mobility_score
    else:
        score -= 0.15 * mobility_score

   
    if board.is_check():
        if board.turn == chess.WHITE:
            score -= 20   # white is in check
        else:
            score += 20   # black is in check

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