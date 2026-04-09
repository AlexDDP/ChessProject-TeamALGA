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

    # Iterates over squares with pieces on them 
    for sq,piece in board.piece_map().items():

        # Determine if we are adding or subtracting points
        sign = 1 if piece.color == chess.WHITE else -1
        
        # Base material score 
        score += sign * PIECE_VALUES[piece.piece_type]

        # Defensive Heuristic:
        
        # We skip checking defense for the King to save time
        if piece.piece_type != chess.KING:
            attackers = board.attackers(not piece.color, sq)
            defenders = board.attackers(piece.color, sq)


        if len(defenders) >= len(attackers):
                score += sign * 10

        
    # This mobility_score  gives more option to bot
     # Good for breaking ties
    mobility_score = len(list(board.legal_moves))

        
    # For defensive play there is a focus on the strcutre of the pawns
    # We multiply by 0.1 so a legal move is only worth 1/100th of a Pawn

    if board.turn == chess.WHITE:
        score += mobility_score * 0.1
    else:
        score -= mobility_score * 0.1

    return score