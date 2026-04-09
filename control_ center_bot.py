import chess

CENTER = [chess.D4, chess.E4, chess.D5, chess.E5]

def evaluate(board):
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate():
        return 0

    score = 0

    for sq in CENTER:
        if board.is_attacked_by(chess.WHITE, sq):
            score += 5
        if board.is_attacked_by(chess.BLACK, sq):
            score -= 5

    return score