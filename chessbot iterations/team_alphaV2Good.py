import chess
import chess.polyglot

# --- Evaluation Constants ---
# Material values based on modern chess theory
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# --- Piece-Square Tables (PeSTO-inspired, Middlegame) ---
# These guide pieces to strong squares. Values are from white's perspective.
PST_MG = {
    chess.PAWN: [
        0,   0,   0,   0,   0,   0,   0,   0,
        98, 134,  61,  95,  68, 126,  34, -11,
        -6,   7,  26,  31,  62,  22,  -8, -17,
       -14,  13,   6,  21,  23,  12,  17, -23,
       -27,  -2,  -5,  12,  17,   6,  10, -25,
       -26,  -4,  -4, -10,   3,   3,  33, -12,
       -35,  -1, -20, -23, -15,  24,  38, -22,
         0,   0,   0,   0,   0,   0,   0,   0
    ],
    chess.KNIGHT: [
       -167, -89, -34, -49,  61, -97, -15,-107,
        -73, -41,  72,  36,  23,  62,   7, -17,
        -47,  60,  37,  65,  84, 129,  73,  44,
         -9,  17,  19,  53,  37,  69,  18,  22,
        -13,   4,  16,  13,  28,  19,  21,  -8,
        -23,  -9,  12,  10,  19,  17,  25, -16,
        -29, -53, -12,  -3,  -1,  18, -14, -19,
       -105, -21, -58, -33, -17, -28, -19, -23
    ],
    chess.BISHOP: [
        -29,   4, -82, -37, -25, -42,   7,  -8,
        -26,  16, -18, -13,  30,  59,  18, -47,
        -16,  37,  43,  40,  35,  50,  37,  -2,
         -4,   5,  19,  50,  37,  37,   7,  -2,
         -6,  13,  13,  26,  34,  12,  10,   4,
          0,  15,  15,  15,  14,  27,  18,  10,
          4,  15,  16,   0,   7,  21,  33,   1,
        -33,  -3, -14, -21, -13, -12, -39, -21
    ],
    chess.ROOK: [
         32,  42,  32,  51,  63,   9,  31,  43,
         27,  32,  58,  62,  80,  67,  26,  44,
         -5,  19,  26,  36,  17,  45,  61,  16,
        -24, -11,   7,  26,  24,  35,  -8, -20,
        -36, -26, -12,  -1,   9,  -7,   6, -23,
        -45, -25, -16, -17,   3,   0,  -5, -33,
        -44, -16, -20,  -9,  -1,  11,  -6, -71,
        -19, -13,   1,  17,  16,   7, -37, -26
    ],
    chess.QUEEN: [
        -28,   0,  29,  12,  59,  44,  43,  45,
        -24, -39,  -5,   1, -16,  57,  28,  54,
        -13, -17,   7,   8,  29,  56,  47,  57,
        -27, -27, -16, -16,  -1,  17,  -2,   1,
         -9, -26,  -9, -10,  -2,  -4,   3,  -3,
        -14,   2, -11,  -2,  -5,   2,  14,   5,
        -35,  -8,  11,   2,   8,  15,  -3,   1,
         -1, -18,  -9,  10, -15, -25, -31, -50
    ],
    chess.KING: [
        -65,  23,  16, -15, -56, -34,   2,  13,
         29,  -1, -20,  -7,  -8,  -4, -38, -29,
         -9,  24,   2, -16, -20,   6,  22, -22,
        -17, -20, -12, -27, -30, -25, -14, -36,
        -49,  -1, -27, -39, -46, -44, -33, -51,
        -14, -14, -22, -46, -44, -30, -15, -27,
          1,   7,  -8, -64, -43, -16,   9,   8,
        -15,  36,  12, -54,   8, -28,  24,  14
    ]
}

# --- Endgame Piece-Square Tables ---
PST_EG = {
    chess.PAWN: [
          0,   0,   0,   0,   0,   0,   0,   0,
        178, 173, 158, 134, 147, 132, 165, 187,
         94, 100,  85,  67,  56,  53,  82,  84,
         32,  24,  13,   5,  -2,   4,  17,  17,
         13,   9,  -3,  -7,  -7,  -8,   3,  -1,
          4,   7,  -6,   1,   0,  -5,  -1,  -8,
         13,   8,   8,  10,  13,   0,   2,  -7,
          0,   0,   0,   0,   0,   0,   0,   0
    ],
    chess.KNIGHT: [
        -58, -38, -13, -28, -31, -27, -63, -99,
        -25,  -8, -25,  -2,  -9, -25, -24, -52,
        -24, -20,  10,   9,  -1,  -9, -19, -41,
        -17,   3,  22,  22,  22,  11,   8, -18,
        -18,  -6,  16,  25,  16,  17,   4, -18,
        -23,  -3,  -1,  15,  10,  -3, -20, -22,
        -42, -20, -10,  -5,  -2, -20, -23, -44,
        -29, -51, -23, -15, -22, -18, -50, -64
    ],
    chess.BISHOP: [
        -14, -21, -11,  -8,  -7,  -9, -17, -24,
         -8,  -4,   7, -12,  -3, -13,  -4, -14,
          2,  -8,   0,  -1,  -2,   6,   0,   4,
         -3,   9,  12,   9,  14,  10,   3,   2,
         -6,   3,  13,  19,   7,  10,  -3,  -9,
        -12,  -3,   8,  10,  13,   3,  -7, -15,
        -14, -18,  -7,  -1,   4,  -9, -15, -27,
        -23,  -9, -23,  -5,  -9, -16,  -5, -17
    ],
    chess.ROOK: [
         13,  10,  18,  15,  12,  12,   8,   5,
         11,  13,  13,  11,  -3,   3,   8,   3,
          7,   7,   7,   5,   4,  -3,  -5,  -3,
          4,   3,  13,   1,   2,   1,  -1,   2,
          3,   5,   8,   4,  -5,  -6,  -8, -11,
         -4,   0,  -5,  -1,  -7, -12,  -8, -16,
         -6,  -6,   0,   2,  -9,  -9, -11,  -3,
         -9,   2,   3,  -1,  -5, -13,   4, -20
    ],
    chess.QUEEN: [
         -9,  22,  22,  27,  27,  19,  10,  20,
        -17,  20,  32,  41,  58,  25,  30,   0,
        -20,   6,   9,  49,  47,  35,  19,   9,
          3,  22,  24,  45,  57,  40,  57,  36,
        -18,  28,  19,  47,  31,  34,  12,  11,
        -16, -27,  15,   6,   9,  17,  10,   5,
        -22, -23, -30, -16, -16, -23, -36, -32,
        -33, -28, -22, -43,  -5, -32, -20, -41
    ],
    chess.KING: [
        -74, -35, -18, -18, -11,  15,   4, -17,
        -12,  17,  14,  17,  17,  38,  23,  11,
         10,  17,  23,  15,  20,  45,  44,  13,
         -8,  22,  24,  27,  26,  33,  26,   3,
        -18,  -4,  21,  24,  27,  23,   9, -11,
        -19,  -3,  11,  21,  23,  16,   7,  -9,
        -27, -11,   4,  13,  14,   4,  -5, -17,
        -53, -34, -21, -11, -28, -14, -24, -43
    ]
}

# Game phase calculation (0 = endgame, 24 = opening)
PHASE_WEIGHT = {
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4
}

# Evaluation bonuses
BISHOP_PAIR_BONUS = 30
ROOK_OPEN_FILE = 25
ROOK_SEMI_OPEN = 12
ROOK_SEVENTH_RANK = 15  # Rook on 7th rank bonus
MOBILITY_WEIGHT = 3
PASSED_PAWN_BONUS = [0, 10, 20, 35, 60, 90, 130, 0]  # by rank
DOUBLED_PAWN_PENALTY = 20
ISOLATED_PAWN_PENALTY = 15
KING_ATTACK_WEIGHT = 10  # Bonus for attacking enemy king zone
TEMPO_BONUS = 15  # Small bonus for having the move

# Transposition table for memoization
_TT_CACHE = {}
_TT_MAX_SIZE = 500000

def _get_game_phase(board):
    """Calculate game phase (0-24). Higher = opening/middlegame, lower = endgame."""
    phase = 0
    for piece_type, weight in PHASE_WEIGHT.items():
        phase += len(board.pieces(piece_type, chess.WHITE)) * weight
        phase += len(board.pieces(piece_type, chess.BLACK)) * weight
    return min(phase, 24)

def _pst_value(piece_type, square, color, phase):
    """Get piece-square table value, interpolated between middlegame and endgame."""
    sq = square if color == chess.WHITE else (square ^ 56)  # Flip for black
    
    if piece_type not in PST_MG or piece_type not in PST_EG:
        return 0
    
    mg_val = PST_MG[piece_type][sq]
    eg_val = PST_EG[piece_type][sq]
    
    # Interpolate based on game phase
    return (mg_val * phase + eg_val * (24 - phase)) // 24

def evaluate(board):
    """
    Sophisticated evaluation function combining multiple chess heuristics.
    Returns a score from white's perspective (positive = white better).
    """
    # Terminal positions
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    
    # Draws - but penalize them slightly if we're ahead
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    # Penalize positions heading toward repetition draw
    if board.is_repetition(2):  # Position occurred twice already
        # If we're winning, strongly avoid the draw
        # This quick material check helps decide if draw is acceptable
        material_balance = 0
        for pt in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            material_balance += len(board.pieces(pt, chess.WHITE)) * PIECE_VALUES[pt]
            material_balance -= len(board.pieces(pt, chess.BLACK)) * PIECE_VALUES[pt]
        
        # Heavily penalize repetition if we're ahead
        if material_balance > 50:  # White is ahead
            return -150  # Bad for white to draw
        elif material_balance < -50:  # Black is ahead
            return 150  # Bad for black to draw
        else:
            return 0  # Equal, draw is fine
    
    if board.can_claim_draw():
        return 0
    
    # Check TT cache
    zobrist = chess.polyglot.zobrist_hash(board)
    if zobrist in _TT_CACHE:
        return _TT_CACHE[zobrist]
    
    score = 0
    phase = _get_game_phase(board)
    
    # --- Material and Piece-Square Tables ---
    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN, chess.KING]:
        for square in board.pieces(piece_type, chess.WHITE):
            score += PIECE_VALUES[piece_type]
            score += _pst_value(piece_type, square, chess.WHITE, phase)
        
        for square in board.pieces(piece_type, chess.BLACK):
            score -= PIECE_VALUES[piece_type]
            score -= _pst_value(piece_type, square, chess.BLACK, phase)
    
    # --- Bishop Pair Bonus ---
    if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
        score += BISHOP_PAIR_BONUS
    if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
        score -= BISHOP_PAIR_BONUS
    
    # --- Pawn Structure ---
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)
    
    # Pawn analysis for white
    for sq in white_pawns:
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        
        # Doubled pawns
        if len([s for s in white_pawns if chess.square_file(s) == file]) > 1:
            score -= DOUBLED_PAWN_PENALTY
        
        # Isolated pawns
        adjacent_files = [file - 1, file + 1]
        if not any(chess.square_file(s) in adjacent_files for s in white_pawns):
            score -= ISOLATED_PAWN_PENALTY
        
        # Passed pawns
        is_passed = True
        for enemy_sq in black_pawns:
            enemy_file = chess.square_file(enemy_sq)
            enemy_rank = chess.square_rank(enemy_sq)
            if abs(enemy_file - file) <= 1 and enemy_rank > rank:
                is_passed = False
                break
        if is_passed:
            score += PASSED_PAWN_BONUS[rank]
    
    # Pawn analysis for black
    for sq in black_pawns:
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        
        if len([s for s in black_pawns if chess.square_file(s) == file]) > 1:
            score += DOUBLED_PAWN_PENALTY
        
        adjacent_files = [file - 1, file + 1]
        if not any(chess.square_file(s) in adjacent_files for s in black_pawns):
            score += ISOLATED_PAWN_PENALTY
        
        is_passed = True
        for enemy_sq in white_pawns:
            enemy_file = chess.square_file(enemy_sq)
            enemy_rank = chess.square_rank(enemy_sq)
            if abs(enemy_file - file) <= 1 and enemy_rank < rank:
                is_passed = False
                break
        if is_passed:
            score -= PASSED_PAWN_BONUS[7 - rank]
    
    # --- Rook Placement ---
    for rook_sq in board.pieces(chess.ROOK, chess.WHITE):
        file = chess.square_file(rook_sq)
        rank = chess.square_rank(rook_sq)
        
        # Open file (no pawns)
        if not any(chess.square_file(s) == file for s in white_pawns | black_pawns):
            score += ROOK_OPEN_FILE
        # Semi-open file (no friendly pawns)
        elif not any(chess.square_file(s) == file for s in white_pawns):
            score += ROOK_SEMI_OPEN
        
        # Rook on 7th rank (often strong)
        if rank == 6:  # 7th rank for white (0-indexed)
            score += ROOK_SEVENTH_RANK
    
    for rook_sq in board.pieces(chess.ROOK, chess.BLACK):
        file = chess.square_file(rook_sq)
        rank = chess.square_rank(rook_sq)
        
        if not any(chess.square_file(s) == file for s in white_pawns | black_pawns):
            score -= ROOK_OPEN_FILE
        elif not any(chess.square_file(s) == file for s in black_pawns):
            score -= ROOK_SEMI_OPEN
        
        if rank == 1:  # 2nd rank for black (7th from their perspective)
            score -= ROOK_SEVENTH_RANK
    
    # --- King Safety / Attack ---
    # In middlegame, reward attacking the enemy king zone
    if phase > 12:  # Middlegame
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        
        if white_king is not None and black_king is not None:
            # Count attackers near enemy king
            white_king_zone = [white_king + d for d in [-9, -8, -7, -1, 0, 1, 7, 8, 9] 
                              if 0 <= white_king + d < 64]
            black_king_zone = [black_king + d for d in [-9, -8, -7, -1, 0, 1, 7, 8, 9] 
                              if 0 <= black_king + d < 64]
            
            # Black attacks on white king
            black_attacks = sum(1 for sq in white_king_zone if board.is_attacked_by(chess.BLACK, sq))
            # White attacks on black king
            white_attacks = sum(1 for sq in black_king_zone if board.is_attacked_by(chess.WHITE, sq))
            
            score += (white_attacks - black_attacks) * KING_ATTACK_WEIGHT
    
    # --- Mobility ---
    original_turn = board.turn
    
    board.turn = chess.WHITE
    white_mobility = board.legal_moves.count()
    
    board.turn = chess.BLACK
    black_mobility = board.legal_moves.count()
    
    board.turn = original_turn
    
    score += (white_mobility - black_mobility) * MOBILITY_WEIGHT
    
    # --- Tempo Bonus ---
    # Small bonus for the side to move (encourages initiative)
    if board.turn == chess.WHITE:
        score += TEMPO_BONUS
    else:
        score -= TEMPO_BONUS
    
    # Cache result
    if len(_TT_CACHE) < _TT_MAX_SIZE:
        _TT_CACHE[zobrist] = score
    
    return score

def move_value(board, move):
    """
    MVV-LVA move ordering for efficient alpha-beta pruning.
    Prioritizes captures of valuable pieces with less valuable attackers.
    """
    score = 0
    
    # Captures
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if victim and attacker:
            score = PIECE_VALUES[victim.piece_type] * 10 - PIECE_VALUES[attacker.piece_type]
    
    # Promotions
    if move.promotion:
        score += PIECE_VALUES.get(move.promotion, 0)
    
    return score

def quiescence_search(board, alpha, beta, maximizing):
    """
    Quiescence search to avoid horizon effect.
    Only searches tactically forcing moves (captures).
    """
    stand_pat = evaluate(board)
    
    if maximizing:
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
        
        # Only search captures
        captures = [m for m in board.legal_moves if board.is_capture(m)]
        captures.sort(key=lambda m: move_value(board, m), reverse=True)
        
        for move in captures:
            board.push(move)
            score = quiescence_search(board, alpha, beta, False)
            board.pop()
            
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return alpha
    else:
        if stand_pat <= alpha:
            return alpha
        beta = min(beta, stand_pat)
        
        captures = [m for m in board.legal_moves if board.is_capture(m)]
        captures.sort(key=lambda m: move_value(board, m), reverse=True)
        
        for move in captures:
            board.push(move)
            score = quiescence_search(board, alpha, beta, True)
            board.pop()
            
            beta = min(beta, score)
            if beta <= alpha:
                break
        return beta

def minimax(board, depth, alpha, beta, maximizing):
    """
    Minimax with alpha-beta pruning.
    Uses move ordering to maximize pruning efficiency.
    """
    if depth == 0:
        return quiescence_search(board, alpha, beta, maximizing)
    
    # Generate and order moves
    moves = list(board.legal_moves)
    moves.sort(key=lambda m: move_value(board, m), reverse=True)
    
    if maximizing:
        best_score = -float('inf')
        for move in moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break  # Beta cutoff
        return best_score
    else:
        best_score = float('inf')
        for move in moves:
            board.push(move)
            score = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            
            best_score = min(best_score, score)
            beta = min(beta, best_score)
            if beta <= alpha:
                break  # Alpha cutoff
        return best_score

def get_next_move(board: chess.Board, color: chess.Color, depth: int = 3) -> chess.Move:
    """
    Entry point for the chess bot.
    Finds the best move using minimax with alpha-beta pruning.
    
    DO NOT MODIFY THIS FUNCTION'S SIGNATURE.
    """
    # Clear cache periodically to prevent memory issues
    global _TT_CACHE
    if len(_TT_CACHE) > _TT_MAX_SIZE:
        _TT_CACHE.clear()
    
    best_move = None
    maximizing = (color == chess.WHITE)
    best_score = -float('inf') if maximizing else float('inf')
    
    # Generate and order moves for root
    moves = list(board.legal_moves)
    if not moves:
        return None
    
    moves.sort(key=lambda m: move_value(board, m), reverse=True)
    
    # Track multiple good moves to avoid always picking the first one
    good_moves = []
    
    # Search each move
    for move in moves:
        board.push(move)
        score = minimax(board, depth - 1, -float('inf'), float('inf'), not maximizing)
        board.pop()
        
        # Add small randomness to break ties (helps avoid repetition)
        import random
        score += random.uniform(-0.5, 0.5)
        
        if maximizing:
            if score > best_score:
                best_score = score
                best_move = move
                good_moves = [move]
            elif abs(score - best_score) < 1.0:  # Within 1 centipawn
                good_moves.append(move)
        else:
            if score < best_score:
                best_score = score
                best_move = move
                good_moves = [move]
            elif abs(score - best_score) < 1.0:
                good_moves.append(move)
    
    # If multiple moves are nearly equal, add variety
    if len(good_moves) > 1 and random.random() < 0.15:  # 15% chance to pick alternate
        return random.choice(good_moves)
    
    return best_move if best_move else moves[0]

if __name__ == '__main__':
    b = chess.Board()
    move = get_next_move(b, chess.WHITE, depth=3)
    print(f"[team_alpha_improved] Move: {b.san(move)}")
