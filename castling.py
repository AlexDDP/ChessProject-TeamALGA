import chess

# ── Piece values (centipawns) ─────────────────────────────────────────────────
PIECE_VALUES = {
    chess.PAWN:   10,
    chess.KNIGHT: 30,
    chess.BISHOP: 30,
    chess.ROOK:   50,
    chess.QUEEN:  90,
    chess.KING:   200,
}


# ── Heuristic ─────────────────────────────────────────────────────────────────
def evaluate(board: chess.Board) -> float:

    if board.is_checkmate():
        # The side to move is in checkmate — they lose
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0

    for piece_type, value in PIECE_VALUES.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

    # Your code goes here

    # ───────────────────────────────────────────────

    w_king_sq = board.king(chess.WHITE)
    b_king_sq = board.king(chess.BLACK)


    # Checks castling rights for each colour independently, regardless of whose turn it is.
    def can_castle_kingside(board, color):
        if not board.has_kingside_castling_rights(color):
            return False
        f_sq = chess.F1 if color == chess.WHITE else chess.F8
        g_sq = chess.G1 if color == chess.WHITE else chess.G8
        if board.piece_at(f_sq) is not None or board.piece_at(g_sq) is not None:
            return False
        # If it's this color's turn, also verify no check/attack issues
        if board.turn == color:
            for move in board.legal_moves:
                if board.is_kingside_castling(move):
                    return True
            return False
        return True


    # ───────────────────────────────────────────────
    # Catsling Rewards
    # ─────────────────────────────────────────────── 

    CASTLING_BONUS = 100
    CASTLING_RIGHTS_BONUS = 15

    # Reward castling
    if w_king_sq in {chess.G1}:
        score += CASTLING_BONUS
    if b_king_sq in {chess.G8}:
        score -= CASTLING_BONUS

    # Reward castling rights
    if board.has_castling_rights(chess.WHITE):
        score += CASTLING_RIGHTS_BONUS
    if board.has_castling_rights(chess.BLACK):
        score -= CASTLING_RIGHTS_BONUS

    # Strong reward when castling is available
    if can_castle_kingside(board, chess.WHITE):
        score += 40
    if can_castle_kingside(board, chess.BLACK):
        score -= 40  


    # ───────────────────────────────────────────────
    # Encourage castling when king and rook are ready
    # ───────────────────────────────────────────────
    if w_king_sq == chess.E1 and board.piece_at(chess.F1) is None and board.piece_at(chess.G1) is None:
        score += 50

    if b_king_sq == chess.E8 and board.piece_at(chess.F8) is None and board.piece_at(chess.G8) is None:
        score -= 50


    # ───────────────────────────────────────────────
    # BISHOP FREEDOM BONUS (encourages pawn pushes)
    # ───────────────────────────────────────────────

    BISHOP_FREEDOM = 20

    # White bishop on f1
    if board.piece_at(chess.F1) == chess.Piece(chess.BISHOP, chess.WHITE):
        if board.piece_at(chess.E2) != chess.Piece(chess.PAWN, chess.WHITE):
            score += BISHOP_FREEDOM

    # Black bishop on f8
    if board.piece_at(chess.F8) == chess.Piece(chess.BISHOP, chess.BLACK):
        if board.piece_at(chess.E7) != chess.Piece(chess.PAWN, chess.BLACK):
            score -= BISHOP_FREEDOM


    # ───────────────────────────────────────────────
    # DEVELOPMENT BONUS (encourages castling setup)
    # ───────────────────────────────────────────────

    UNDEVELOPED_MINOR_PENALTY = 30

    # White knights
    if board.piece_at(chess.G1) == chess.Piece(chess.KNIGHT, chess.WHITE):
        score -= UNDEVELOPED_MINOR_PENALTY

    # White bishops
    if board.piece_at(chess.F1) == chess.Piece(chess.BISHOP, chess.WHITE):
        score -= UNDEVELOPED_MINOR_PENALTY

    # Black knights
    if board.piece_at(chess.G8) == chess.Piece(chess.KNIGHT, chess.BLACK):
        score += UNDEVELOPED_MINOR_PENALTY

    # Black bishops
    if board.piece_at(chess.F8) == chess.Piece(chess.BISHOP, chess.BLACK):
        score += UNDEVELOPED_MINOR_PENALTY


    # ───────────────────────────────────────────────
    # King still in center after move 5
    # ───────────────────────────────────────────────
    if board.fullmove_number >= 5:
        if w_king_sq in {chess.E1, chess.D1}:
            score -= 50
        if b_king_sq in {chess.E8, chess.D8}:
            score += 50


    # ───────────────────────────────────────────────
    # Pawn shield
    # ───────────────────────────────────────────────
   
    PAWN_SHIELD_WEIGHT = 8

    def pawn_shield(board, color):
        king_sq = board.king(color)
        if king_sq is None:
            return 0
        file = chess.square_file(king_sq)
        rank = chess.square_rank(king_sq)
        direction = 1 if color == chess.WHITE else -1
        shield = 0
        for df in [-1, 0, 1]:
            f = file + df
            r = rank + direction
            if 0 <= f < 8 and 0 <= r < 8:
                sq = chess.square(f, r)
                if board.piece_at(sq) == chess.Piece(chess.PAWN, color):
                    shield += 1
        return shield

    score += PAWN_SHIELD_WEIGHT * pawn_shield(board, chess.WHITE)
    score -= PAWN_SHIELD_WEIGHT * pawn_shield(board, chess.BLACK)

    # Mobility bonus
    score += 0.1 * board.legal_moves.count()

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