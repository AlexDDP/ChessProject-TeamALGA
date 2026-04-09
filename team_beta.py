"""
team_alpha.py  —  Chess Bot using Minimax + Alpha-Beta Pruning
Heuristic: Material value

Install dependency:  pip install python-chess
"""

import chess


# ── Piece values (centipawns) ─────────────────────────────────────────────────
PIECE_VALUES = {
    chess.PAWN:   10,
    chess.KNIGHT: 20,
    chess.BISHOP: 20,
    chess.ROOK:   50,
    chess.QUEEN:  90,
    chess.KING:   200,
}


# Bonuses for pieces attacing the center
ATTACKING_BONUS = {
    chess.PAWN: 1.5,
    chess.KNIGHT: 3.0,
    chess.BISHOP: 2.5,
    chess.ROOK: 1.5,
    chess.QUEEN: 1.0,
    chess.KING: 0.5,
}

# Bonuses for the piece occupying the central sqaures
OCCUPANCY_BONUS = {
    chess.PAWN: 8.0,
    chess.KNIGHT: 10.0,
    chess.BISHOP: 7.0,
    chess.ROOK: 5.0,
    chess.QUEEN: 3.0,
    chess.KING: 0.0,
}



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


# ── Heuristic ─────────────────────────────────────────────────────────────────
def evaluate(board: chess.Board) -> float:

    # Modified evaluate function which takes cetner control heuristic into account

    """

    Material:  Sum of piece values for White minus Black.

    Score > 0  =>  White is better.
    Score < 0  =>  Black is better.
    """
    if board.is_checkmate():
        # The side to move is in checkmate — they lose
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0

    
    # ── Material ─────────────────────────────────────────
    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

    # ── Center Control ───────────────────────────────────
    score += control_center(board)

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