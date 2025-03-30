import streamlit as st
import chess
import chess.pgn
import io
from PIL import Image
import chess.svg
import cairosvg

# Utility: Convert board to PNG for Streamlit
def render_board(board, last_move=None, orientation=chess.WHITE):
    # Lichess-like theme colors
    square_light = "#f0d9b5"
    square_dark = "#b58863"
    check_square = "#ff0000"
    arrow_color = "#00ff00"
    lastmove_color = "rgba(155, 199, 0, 0.41)"
    
    svg = chess.svg.board(
        board=board, 
        lastmove=last_move, 
        size=400,
        orientation=orientation,
        colors={
            'square light': square_light,
            'square dark': square_dark,
            'square light lastmove': lastmove_color,
            'square dark lastmove': lastmove_color,
            'margin': 'white',
            'coord': '#888888',
            'arrow': arrow_color,
        }
    )
    png = cairosvg.svg2png(bytestring=svg)
    return Image.open(io.BytesIO(png))

# ORIENT analysis
def orient_analysis(board, color, move_san, move_number):
    lines = []
    player = "White" if color == chess.WHITE else "Black"
    lines.append(f"### 🧠 Move {move_number}: {player} plays `{move_san}`\n")

    # KINGS
    lines.append("**• Kings**")
    for side in [color, not color]:
        side_str = "Own" if side == color else "Opponent"
        king_square = board.king(side)
        file_open = all(
            (board.piece_at(chess.square(chess.square_file(king_square), r)) is None or 
             board.piece_at(chess.square(chess.square_file(king_square), r)).piece_type == chess.KING)
            for r in range(8)
        )
        lines.append(f"- {side_str} king on open file: {'Yes' if file_open else 'No'}")

    # Checks and checkmates
    threats = []
    for move in board.legal_moves:
        if board.gives_check(move):
            board.push(move)
            if board.is_checkmate():
                threats.append(f"Checkmate threat: {move}")
            board.pop()
    checks = [move for move in board.legal_moves if board.gives_check(move)]
    if checks:
        check_moves = [board.san(move) for move in checks]
        lines.append(f"- Available checks: {', '.join(check_moves)}")
    else:
        lines.append("- Available checks: None")
    if threats:
        lines.append(f"- ❗ {', '.join(threats)}")
    
    # THINGS section - Analyzing tactical weaknesses in the position
    lines.append("\n**• Things**")
    
    # Initialize empty lists to track different types of tactical weaknesses
    hanging = []  # Pieces that are attacked but not defended
    loose = []    # Pieces that are not defended (but not currently attacked)
    overloaded = []  # Pieces with only one defender (vulnerable to overloading tactics)
    weak = []     # Specifically for pawns that lack defenders
    
    # Iterate through all squares on the chess board
    for square in chess.SQUARES:
        # Get the piece at the current square
        piece = board.piece_at(square)
        
        # Skip empty squares and opponent's pieces
        if not piece or piece.color != color:
            continue
            
        # Find all attackers (opponent's pieces) targeting this square
        attackers = board.attackers(not color, square)
        
        # Find all defenders (own pieces) protecting this square
        defenders = board.attackers(color, square)
        
        # Case 1: Hanging piece - attacked with no defenders
        if attackers and not defenders:
            # Format: piece_symbol@square_name (e.g., "P@e4")
            hanging.append(f"{piece.symbol()}@{chess.square_name(square)}")
            
        # Case 2: Loose piece - not attacked but also not defended
        elif not defenders:
            loose.append(f"{piece.symbol()}@{chess.square_name(square)}")
            
        # Case 3: Potentially overloaded defender - a piece that defends multiple pieces
        # We need to track the defenders themselves, not the pieces being defended
        elif len(defenders) == 1:
            # Get the defender square
            defender_square = list(defenders)[0]
            # Add the defender to our tracking (format: piece@square)
            defender_piece = board.piece_at(defender_square)
            overloaded_key = f"{defender_piece.symbol()}@{chess.square_name(defender_square)}"
            if overloaded_key not in overloaded:
                # Count how many pieces this defender is protecting
                defending_count = sum(1 for sq in chess.SQUARES 
                                    if board.piece_at(sq) and board.piece_at(sq).color == color 
                                    and defender_square in board.attackers(color, sq))
                if defending_count > 1:  # Only add if defending multiple pieces
                    overloaded.append(overloaded_key)
            
        # Case 4: Weak pawn - specifically tracking pawns without defenders
        # Pawns are particularly important to track as they form the structure of the position
        if piece.piece_type == chess.PAWN and not defenders:
            weak.append(chess.square_name(square))

    # Add formatted results to the analysis output
    # For each category, join the items with commas or show "None" if empty
    lines.append(f"- Hanging pieces: {', '.join(hanging) if hanging else 'None'}")
    lines.append(f"- Loose pieces: {', '.join(loose) if loose else 'None'}")
    lines.append(f"- Overloaded pieces: {', '.join(overloaded) if overloaded else 'None'}")
    lines.append(f"- Weak pawns: {', '.join(weak) if weak else 'None'}")

    # STRINGS
    lines.append("\n**• Strings**")
    # Find pins - identify specific pieces that are pinned
    pin_details = []
    for sq in chess.SQUARES:
        if board.piece_at(sq) and board.piece_at(sq).color == color and board.is_pinned(color, sq):
            piece = board.piece_at(sq)
            # Get the pinner (usually a bishop, rook, or queen)
            pinner_square = None
            # Check along rays from the king through the pinned piece
            king_square = board.king(color)
            ray_direction = chess.square_rank(sq) - chess.square_rank(king_square), chess.square_file(sq) - chess.square_file(king_square)
            
            # Normalize the direction
            if ray_direction[0] != 0:
                ray_direction = (ray_direction[0] // abs(ray_direction[0]), ray_direction[1] // abs(ray_direction[0]) if ray_direction[1] != 0 else 0)
            elif ray_direction[1] != 0:
                ray_direction = (0, ray_direction[1] // abs(ray_direction[1]))
                
            # Follow the ray to find the pinner
            current_rank, current_file = chess.square_rank(sq) + ray_direction[0], chess.square_file(sq) + ray_direction[1]
            while 0 <= current_rank < 8 and 0 <= current_file < 8:
                current_sq = chess.square(current_file, current_rank)
                if board.piece_at(current_sq) and board.piece_at(current_sq).color != color:
                    pinner_square = current_sq
                    break
                current_rank += ray_direction[0]
                current_file += ray_direction[1]
                
            if pinner_square:
                pinner = board.piece_at(pinner_square)
                pin_details.append(f"{piece.symbol()}@{chess.square_name(sq)} pinned by {pinner.symbol()}@{chess.square_name(pinner_square)}")
    
    # Find potential discovered checks
    discovery_details = []
    for move in board.legal_moves:
        from_square = move.from_square
        piece = board.piece_at(from_square)
        if piece:
            # Make the move on the board to see if it reveals a check
            board.push(move)
            
            # Check if the move results in a check
            if board.is_check():
                # Get the opponent's king square
                king_square = board.king(not color)
                
                # The issue with the original code is here:
                # board.is_attacked_by(color, king_square) only tells us if the king is attacked,
                # but doesn't identify which piece is attacking.
                # We need to find all attackers of the king square
                attackers = board.attackers(color, king_square)
                
                # Loop through all attackers to find the one that's giving the discovered check
                for attacker_square in attackers:
                    # If the attacker is not the piece that just moved, it's a discovered check
                    if attacker_square != move.to_square:
                        attacker = board.piece_at(attacker_square)
                        discovery_details.append(f"{piece.symbol()}@{chess.square_name(from_square)} moving reveals check from {attacker.symbol()}@{chess.square_name(attacker_square)}")
                        break
            
            # Undo the move to restore the board state
            board.pop()
    # Add formatted results to the analysis output
    lines.append(f"- Potential pins: {', '.join(pin_details) if pin_details else 'None'}")
    lines.append(f"- Potential discovered checks: {', '.join(discovery_details) if discovery_details else 'None'}")

    return "\n".join(lines)

# Main app
st.set_page_config(page_title="WhatTheMove", layout="wide")
st.title("♟️ WhatTheMove")
st.caption("Minimalist Chess Thought Analyzer")

# Move file uploader to sidebar
with st.sidebar:
    st.header("Game Upload")
    uploaded_file = st.file_uploader("Upload a PGN file", type=["pgn"])
    
    # Board orientation options
    st.header("Board Settings")
    if "board_orientation" not in st.session_state:
        st.session_state.board_orientation = chess.WHITE
    
    # Auto-flip option
    auto_flip = st.checkbox("Auto-flip board (current player at bottom)", value=False)
    
    # Add some helpful instructions in the sidebar
    with st.expander("How to use"):
        st.write("""
        1. Upload a PGN chess game file
        2. Navigate through moves using the buttons or move list
        3. View analysis from both White and Black perspectives
        4. Explore the ORIENT analysis for each position
        5. Use the 'Flip Board' button or enable auto-flip to change perspective
        """)

# Main content area
if uploaded_file:
    pgn = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
    game = chess.pgn.read_game(pgn)
    moves = list(game.mainline_moves())

    if "move_index" not in st.session_state:
        st.session_state.move_index = 0

    col1, col2, col3 = st.columns([1, 1.2, 2])

    # MOVE LIST - Prettier version with white and black moves on same line
    with col1:
        st.subheader("Move List")
        
        # Generate move pairs (white and black)
        board = game.board()
        move_pairs = []
        white_moves = []
        black_moves = []
        
        for i, move in enumerate(moves):
            san = board.san(move)
            if i % 2 == 0:  # White's move
                white_moves.append(san)
            else:  # Black's move
                black_moves.append(san)
            board.push(move)
        
        # Make sure lists are same length for pairing
        if len(white_moves) > len(black_moves):
            black_moves.append("")
            
        move_pairs = list(zip(white_moves, black_moves))
        
        # Create a scrollable container with fixed height
        move_list_container = st.container()
        
        # Apply CSS for scrolling and compact buttons
        st.markdown("""
            <style>
                /* Make buttons smaller */
                .stButton > button {
                    padding: 0.15rem 0.5rem;
                    font-size: 0.8rem;
                    line-height: 1;
                }
                
                /* Add spacing between move rows */
                .row-widget.stButton {
                    margin-bottom: 0.15rem;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Create a scrollable container
        move_list = st.container(height=400)
        
        with move_list:
            # Display moves in a compact format
            for move_num, (white_move, black_move) in enumerate(move_pairs, 1):
                cols = st.columns([0.2, 0.4, 0.4])
                
                # Move number
                cols[0].write(f"{move_num}.")
                
                # White move
                if white_move:
                    white_index = (move_num - 1) * 2
                    white_active = st.session_state.move_index == white_index
                    if cols[1].button(
                        white_move, 
                        key=f"white_{move_num}", 
                        use_container_width=True,
                        type="primary" if white_active else "secondary"
                    ):
                        st.session_state.move_index = white_index
                        st.rerun()
                
                # Black move
                if black_move:
                    black_index = (move_num - 1) * 2 + 1
                    black_active = st.session_state.move_index == black_index
                    if cols[2].button(
                        black_move, 
                        key=f"black_{move_num}", 
                        use_container_width=True,
                        type="primary" if black_active else "secondary"
                    ):
                        st.session_state.move_index = black_index
                        st.rerun()

    # CHESSBOARD
    with col2:
        st.subheader("Live Board")
        board = game.board()
        last_move = None
        for i, move in enumerate(moves[:st.session_state.move_index + 1]):
            last_move = move
            board.push(move)
        
        # Determine board orientation
        if auto_flip:
            # Set orientation based on whose turn it is
            st.session_state.board_orientation = board.turn
        
        # Render the board with the current orientation
        st.image(
            render_board(
                board, 
                last_move=last_move, 
                orientation=st.session_state.board_orientation
            ), 
            use_container_width=True
        )
        
        # Navigation and flip buttons
        col_prev, col_next, col_flip = st.columns([1, 1, 1])
        if col_prev.button("⬅ Prev", use_container_width=True):
            if st.session_state.move_index > 0:
                st.session_state.move_index -= 1
                st.rerun()
                
        if col_next.button("Next ➡", use_container_width=True):
            if st.session_state.move_index < len(moves) - 1:
                st.session_state.move_index += 1
                st.rerun()
        
        # Flip board button
        if col_flip.button("🔄 Flip Board", use_container_width=True):
            st.session_state.board_orientation = not st.session_state.board_orientation
            st.rerun()

    # ANALYSIS
    with col3:
        st.subheader("Analysis")
        if st.session_state.move_index < len(moves):
            # Get the move that was just played
            move = moves[st.session_state.move_index]
            
            # Set up the board to the position before the move
            board = game.board()
            for i in range(st.session_state.move_index):
                board.push(moves[i])
            
            # Get whose turn it was before the move (the player who made the move)
            player_who_moved = board.turn
            san = board.san(move)
            
            # Push the move to get to the current position
            board.push(move)
            
            # After the move is played, it's the other player's turn
            next_to_move = board.turn
            player_name = "White" if next_to_move == chess.WHITE else "Black"
            player_who_moved_name = "White" if player_who_moved == chess.WHITE else "Black"
            
            # Display whose perspective we're analyzing from
            st.markdown(f"## Analysis from {player_name}'s Perspective")
            st.markdown(f"*After {player_who_moved_name} played {san}, it's {player_name}'s turn to move*")
            
            # Create tabs for defense and offense perspectives
            defense_tab, offense_tab = st.tabs(["Defense", "Offense"])
            
            # Defense analysis - looking at your own vulnerabilities
            with defense_tab:
                st.markdown(f"### Defensive Analysis for {player_name}")
                st.markdown("*Analyzing your own vulnerabilities and safety*")
                
                # King safety
                st.markdown("**• King Safety**")
                king_square = board.king(next_to_move)
                file_open = all(
                    (board.piece_at(chess.square(chess.square_file(king_square), r)) is None or 
                     board.piece_at(chess.square(chess.square_file(king_square), r)).piece_type == chess.KING)
                    for r in range(8)
                )
                st.markdown(f"- Your king on open file: {'Yes ⚠️' if file_open else 'No'}")
                
                # Checks against you
                checks_against_you = []
                for move in board.legal_moves:
                    if board.gives_check(move):
                        checks_against_you.append(board.san(move))
                st.markdown(f"- Checks opponent can play: {', '.join(checks_against_you) if checks_against_you else 'None'}")
                
                # Your vulnerable pieces
                st.markdown("**• Your Vulnerable Pieces**")
                hanging, loose, overloaded, weak = [], [], [], []
                for square in chess.SQUARES:
                    piece = board.piece_at(square)
                    if not piece or piece.color != next_to_move:
                        continue
                    attackers = board.attackers(not next_to_move, square)
                    defenders = board.attackers(next_to_move, square)
                    if attackers and not defenders:
                        hanging.append(f"{piece.symbol()}@{chess.square_name(square)}")
                    elif not defenders:
                        loose.append(f"{piece.symbol()}@{chess.square_name(square)}")
                    elif len(defenders) == 1:
                        overloaded.append(f"{piece.symbol()}@{chess.square_name(square)}")
                    if piece.piece_type == chess.PAWN and not defenders:
                        weak.append(chess.square_name(square))
                
                st.markdown(f"- Your hanging pieces: {', '.join(hanging) if hanging else 'None'}")
                st.markdown(f"- Your loose pieces: {', '.join(loose) if loose else 'None'}")
                st.markdown(f"- Your overloaded pieces: {', '.join(overloaded) if overloaded else 'None'}")
                st.markdown(f"- Your weak pawns: {', '.join(weak) if weak else 'None'}")
                
                # Potential pins against you
                st.markdown("**• Potential Pins Against You**")
                pins_against_you = []
                for sq in chess.SQUARES:
                    if board.piece_at(sq) and board.piece_at(sq).color == next_to_move and board.is_pinned(next_to_move, sq):
                        piece = board.piece_at(sq)
                        pins_against_you.append(f"{piece.symbol()}@{chess.square_name(sq)}")
                st.markdown(f"- Your pinned pieces: {', '.join(pins_against_you) if pins_against_you else 'None'}")
                
                # Opponent's potential discoveries
                st.markdown("**• Opponent's Potential Discoveries**")
                opponent_discoveries = []
                for move in board.legal_moves:
                    if board.is_capture(move):
                        continue  # Skip captures for simplicity
                    board.push(move)
                    if board.is_check():
                        from_square = move.from_square
                        piece = board.piece_at(move.to_square)
                        opponent_discoveries.append(f"{piece.symbol()} from {chess.square_name(from_square)}")
                    board.pop()
                st.markdown(f"- Opponent discoveries: {', '.join(opponent_discoveries) if opponent_discoveries else 'None'}")
            
            # Offense analysis - looking at opponent vulnerabilities
            with offense_tab:
                st.markdown(f"### Offensive Analysis for {player_name}")
                st.markdown("*Analyzing opponent vulnerabilities and your attacking chances*")
                
                # Opponent king safety
                st.markdown("**• Opponent King Safety**")
                opp_king_square = board.king(not next_to_move)
                opp_file_open = all(
                    (board.piece_at(chess.square(chess.square_file(opp_king_square), r)) is None or 
                     board.piece_at(chess.square(chess.square_file(opp_king_square), r)).piece_type == chess.KING)
                    for r in range(8)
                )
                st.markdown(f"- Opponent king on open file: {'Yes 🎯' if opp_file_open else 'No'}")
                
                # Your available checks
                your_checks = []
                for move in board.legal_moves:
                    if board.gives_check(move):
                        your_checks.append(board.san(move))
                st.markdown(f"- Checks you can play: {', '.join(your_checks) if your_checks else 'None'}")
                
                # Opponent vulnerable pieces
                st.markdown("**• Opponent Vulnerable Pieces**")
                opp_hanging, opp_loose, opp_overloaded, opp_weak = [], [], [], []
                for square in chess.SQUARES:
                    piece = board.piece_at(square)
                    if not piece or piece.color != (not next_to_move):
                        continue
                    attackers = board.attackers(next_to_move, square)
                    defenders = board.attackers(not next_to_move, square)
                    if attackers and not defenders:
                        opp_hanging.append(f"{piece.symbol()}@{chess.square_name(square)}")
                    elif not defenders:
                        opp_loose.append(f"{piece.symbol()}@{chess.square_name(square)}")
                    elif len(defenders) == 1:
                        opp_overloaded.append(f"{piece.symbol()}@{chess.square_name(square)}")
                    if piece.piece_type == chess.PAWN and not defenders:
                        opp_weak.append(chess.square_name(square))
                
                st.markdown(f"- Opponent hanging pieces: {', '.join(opp_hanging) if opp_hanging else 'None'}")
                st.markdown(f"- Opponent loose pieces: {', '.join(opp_loose) if opp_loose else 'None'}")
                st.markdown(f"- Opponent overloaded pieces: {', '.join(opp_overloaded) if opp_overloaded else 'None'}")
                st.markdown(f"- Opponent weak pawns: {', '.join(opp_weak) if opp_weak else 'None'}")
                
                # Potential pins you can create
                st.markdown("**• Potential Pins You Can Create**")
                pins_you_can_create = []
                for sq in chess.SQUARES:
                    if board.piece_at(sq) and board.piece_at(sq).color == (not next_to_move) and board.is_pinned(not next_to_move, sq):
                        piece = board.piece_at(sq)
                        pins_you_can_create.append(f"{piece.symbol()}@{chess.square_name(sq)}")
                st.markdown(f"- Opponent pieces you can pin: {', '.join(pins_you_can_create) if pins_you_can_create else 'None'}")
                
                # Your potential discoveries
                st.markdown("**• Your Potential Discoveries**")
                your_discoveries = []
                for move in board.legal_moves:
                    from_square = move.from_square
                    piece = board.piece_at(from_square)
                    if not piece or piece.color != next_to_move:
                        continue
                    board.push(move)
                    if board.is_check():
                        your_discoveries.append(f"{piece.symbol()}@{chess.square_name(from_square)} moving creates discovery")
                    board.pop()
                st.markdown(f"- Your discoveries: {', '.join(your_discoveries) if your_discoveries else 'None'}")
else:
    # Center the info message when no file is uploaded
    st.markdown(
        """
        <div style="display: flex; justify-content: center; align-items: center; height: 70vh;">
            <div style="text-align: center; padding: 2rem; border-radius: 0.5rem; background-color: #f8f9fa; max-width: 500px;">
                <h2>Welcome to WhatTheMove</h2>
                <p>Upload a PGN file from the sidebar to analyze your chess game.</p>
                <p>The analysis will show you the thought process for each move using the ORIENT framework.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
