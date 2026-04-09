import chess

PIECE_VALUES = {
    chess.PAWN: 10,
    chess.KNIGHT: 20,
    chess.BISHOP: 20,
    chess.ROOK: 50,
    chess.QUEEN: 90,
    chess.KING: 200,
}

def evaluate(board):
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate():
        return 0

    score = 0

    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece is None:
            continue

        attackers = board.attackers(not piece.color, sq)
        defenders = board.attackers(piece.color, sq)

        if len(defenders) >= len(attackers):
            if piece.color == chess.WHITE:
                score += 10
            else:
                score -= 10

    return score