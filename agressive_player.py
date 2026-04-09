import chess

PIECE_VALUES = {
    chess.PAWN: 10, chess.KNIGHT: 30, chess.BISHOP: 30, 
    chess.ROOK: 50, chess.QUEEN: 90
}

# Reduces move repitition
def mobility(board):
    return len(list(board.legal_moves))

def evaluate(board):
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate():
        return 0

    score = 0

    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

        move_mobility = mobility()

        # Rewarding checks for white/black
        # Also takes into account mobility
        if board.turn == chess.WHITE:
            score += mobility * 0.5
        if board.is_check(): score += 50 # Huge bonus for checking black
    else:
        score -= mobility * 0.5
        if board.is_check(): score -= 50 # Huge bonus for checking white

    return score

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