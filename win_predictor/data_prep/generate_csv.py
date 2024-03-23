import chess
import chess.pgn
import numpy as np
import pandas as pd
from pathlib import Path
import os

# Define the mappings
piece_mapping_int = {
    'p': -1, 'b': -2, 'n': -3, 'r': -4, 'q': -5, 'k': -6,
    'P': 1, 'B': 2, 'N': 3, 'R': 4, 'Q': 5, 'K': 6,
    '.': 0
}

piece_mapping_flt = {
    'p': -1/6, 'b': -2/6, 'n': -3/6, 'r': -4/6, 'q': -5/6, 'k': -1,
    'P': 1/6, 'B': 2/6, 'N': 3/6, 'R': 4/6, 'Q': 5/6, 'K': 1,
    '.': 0
}

step = 42

piece_mapping_256 = {
    'p': -1*step, 'b': -2*step, 'n': -3*step, 'r': -4*step, 'q': -5*step, 'k': -6*step,
    'P': 1*step, 'B': 2*step, 'N': 3*step, 'R': 4*step, 'Q': 5*step, 'K': 6*step,
    '.': 0
}

# input/output file
input_pgn_path = "../data/filtered.pgn"
root_output_folder = Path("../text")

# games to be extracted from
total_train_games = 4e2
total_valid_games = 8e1


def board_to_array(board_str: str, side_to_move: chess.Color) -> np.ndarray:
    """
    Convert a string representation of a chess board into a 2D numpy array representation.

    Args:
        board_str (str): A string representation of the chess board.
        side_to_move (chess.Color): The side to move, either chess.WHITE or chess.BLACK.

    Returns:
        np.ndarray: A 2D numpy array representation of the chess board.

    Example:
        board_str = "rnbqkbnr\npppppppp\n........\n........\n........\n........\nPPPPPPPP\nRNBQKBNR"
        side_to_move = chess.WHITE
        board_array = board_to_array(board_str, side_to_move)
        print(board_array)
        # Output:
        # [[-2 -3 -4 -5 -6 -4 -3 -2]
        #  [-1 -1 -1 -1 -1 -1 -1 -1]
        #  [ 0  0  0  0  0  0  0  0]
        #  [ 0  0  0  0  0  0  0  0]
        #  [ 0  0  0  0  0  0  0  0]
        #  [ 0  0  0  0  0  0  0  0]
        #  [ 1  1  1  1  1  1  1  1]
        #  [ 2  3  4  5  6  4  3  2]]
    """
    rows = board_str.strip().split('\n')
    board_array = np.zeros((8, 8), dtype=int)

    for i, row in enumerate(rows):        
        for j, piece_char in enumerate(row.split()):
            board_array[i, j] = piece_mapping_int.get(piece_char, 0)

    if side_to_move == chess.BLACK:
        board_array = -board_array[::-1, :]

    return board_array
    
def output_state(board: chess.Board, result: str, game_number: int, df : pd.DataFrame) -> None:
    """
    Output the state of a chess board as an image file.

    Args:
        board (chess.Board): The current state of the chess board.
        result (str): The result of the game.
        output_folder (str): The path to the folder where the image file will be saved.
        game_number (int): The number of the game.

    Returns:
        None

    Example:
        board = chess.Board()
        result = "1-0"
        output_folder = "../images/train/1"
        game_number = 1
        output_state(board, result, output_folder, game_number)
    """
    # get side to move
    side_to_move = board.turn

    # get the current ply number
    ply_number = board.ply()

    # get the side to win
    side_wins = (result == "1-0" and side_to_move == chess.WHITE) or (result == "0-1" and side_to_move == chess.BLACK)

    # converthe board state into an image
    board_array = board_to_array(str(board),side_to_move)

    # Flatten the 2D array into a 1D vector
    flattened_board = board_array.flatten()

    # Data for the new row
    new_row_data = np.concatenate(([game_number,ply_number],flattened_board,[side_wins]))

    # Add new line to the DataFrame
    df.loc[len(df)] = new_row_data

def play_through_game(game, output_folder, game_number, df):
    """
    Iterates through each move in a chess game and outputs the state of the chess board after each move.

    Args:
        game (chess.pgn.Game): The chess game to play through.
        output_folder (str): The path to the folder where the image files will be saved.
        game_number (int): The number of the game.

    Returns:
        None
    """
    board = chess.Board()
    result = game.headers.get("Result", "")
    output_state(board, result, game_number, df)

    for move in game.mainline_moves():
        board.push(move)
        output_state(board, result, game_number, df)

    return

if __name__ == "__main__":

    if not os.path.exists(root_output_folder):
        os.makedirs(root_output_folder)

    train_game_number = -1
    valid_game_number = -1

    # Create Pandas DataFrames
    column_names = ['game_no','ply_no'] + [f'f_{i}' for i in range(1, 65)] + ['result']
    train_df = pd.DataFrame(columns=column_names)
    valid_df = pd.DataFrame(columns=column_names)

    with open(input_pgn_path) as pgn_file:
        game = chess.pgn.read_game(pgn_file)
    
        while game is not None and train_game_number < total_train_games:
            train_game_number += 1
            play_through_game(game, root_output_folder, train_game_number, train_df)
            print(train_game_number, valid_game_number)
            game = chess.pgn.read_game(pgn_file)
                
        # Save the DataFrame to a CSV file
        train_df.to_csv(root_output_folder / "train.csv", index=False)
    
        while game is not None and valid_game_number < total_valid_games:
            valid_game_number += 1
            play_through_game(game, root_output_folder, valid_game_number, valid_df)
            print(train_game_number, valid_game_number)
            game = chess.pgn.read_game(pgn_file)
                
        # Save the DataFrame to a CSV file
        valid_df.to_csv(root_output_folder / "valid.csv", index=False)
