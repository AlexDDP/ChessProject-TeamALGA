import chess

def evaluate(board):
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate():
        return 0

    score = 0

    # Reward checks
    if board.is_check():
        if board.turn == chess.WHITE:
            score -= 50
        else:
            score += 50

    return score