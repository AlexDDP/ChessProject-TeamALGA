import chess

CENTER = [chess.D4, chess.E4, chess.D5, chess.E5]

PIECE_VALUES = {
    chess.PAWN: 10,
    chess.KNIGHT: 30, # Increased value of minor pieces slightly to encourage active play
    chess.BISHOP: 30,
    chess.ROOK: 50,
    chess.QUEEN: 90,
}

def evaluate(board):
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate():
        return 0

    score = 0

    for sq, piece in board.piece_map().items():
        if piece.piece_type != chess.KING:
            sign = 1 if piece.color == chess.WHITE else -1
            score += sign * PIECE_VALUES[piece.piece_type]

    # CENTER CONTROL
    for sq in CENTER:

        # Instead of a flat +5, we give +2 for EVERY piece attacking that square.
        # This encourages the bot to pile pressure on the middle of the board.
        white_attackers = len(board.attackers(chess.WHITE, sq))
        black_attackers = len(board.attackers(chess.BLACK, sq))
        
        score += white_attackers * 2
        score -= black_attackers * 2

    # MOBILITY
    mobility_score = len(list(board.legal_moves))
    
    # We weight this at 0.1 so it acts as a tie-breaker. 
    # It will prefer positions with more moves, but won't hang a Pawn (value 10) just to get them.
    if board.turn == chess.WHITE:
        score += mobility_score * 0.1
    else:
        score -= mobility_score * 0.1

    return score