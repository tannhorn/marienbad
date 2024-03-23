import chess
import chess.pgn
import re
import numpy as np
import json

# input/output file
input_file = "data_path.json"
output_pgn_path = "../data/filtered.pgn"

# games to be extracted from
total_games = 1e4

starting_eval = str(0.3) # for consistency with the rest of evals

pattern = re.compile(r"\[%clk\s(\d{1}:\d{2}:\d{2})\]")

def parse_time_remaining(comment):
    """
    Parses the time remaining from a comment.

    Args:
        comment (str): The comment to parse.

    Returns:
        str: The time remaining in the format HH:MM:SS.
    """
    match = pattern.search(comment)
    if match:
        return match.group(1)
    return None

def parse_evaluation(comment):
    """
    Parses the evaluation value from a comment.

    Args:
        comment (str): The comment containing the evaluation value.

    Returns:
        str or None: The evaluation value extracted from the comment, or None if no evaluation value is found.
    """    
    match = re.match(r"\[%eval\s(.+?)\]", comment)
    if match:
        return match.group(1)
    return None

def first_evaluation(game):
    """
    Returns the evaluation value from the first move of the game.

    Args:
        game (object): The game object containing moves with evaluation comments.

    Returns:
        float or None: The evaluation value from the first move of the game, or None if there is no next move or the comment does not match the expected format.
    """
    next_move = game.next()
    if next_move is not None:
        return parse_evaluation(next_move.comment)
    return None

# based on:
# https://lichess.org/page/accuracy
# https://github.com/lichess-org/lila/pull/11128
# https://github.com/lichess-org/lila/blob/master/modules/analyse/src/main/WinPercent.scala#L23
# https://github.com/lichess-org/lila/blob/master/modules/analyse/src/main/AccuracyPercent.scala#L38-L44
def winpercent(eval: float, side_to_move: int) -> float:
    """
    Calculates the win percentage based on the evaluation score and the side to move.

    Args:
        eval (float): The evaluation score of the position.
        side_to_move (int): The side to move, where 1 represents white and -1 represents black.

    Returns:
        float: The win percentage based on the evaluation score and the side to move.
    """
    rescaled_stm = 2 * side_to_move - 1

    if eval[0] == '#':
        mate_in = int(eval[1:])
        if mate_in * rescaled_stm > 0:
            return 100.0
        else:
            return -100.0
    else:
        sigmoid = 2.0 / (1.0 + np.exp(-0.00368208e2 * rescaled_stm * float(eval)))
        return 50.0 + 50.0 * (sigmoid - 1.0)

def move_accuracy(eval_old,eval,side_to_move):
    """
    Calculates the move accuracy based on the evaluation scores and the side to move.

    Args:
        eval_old (float): The evaluation score of the previous move.
        eval (float): The evaluation score of the current move.
        side_to_move (int): The side to move, where 1 represents white and -1 represents black.

    Returns:
        float: The move accuracy as a percentage.

    Notes:
        The move accuracy is calculated by comparing the win percentages of the previous move and the current move. 
        If the win percentage of the current move is higher than the win percentage of the previous move, the move accuracy is 100%.
        Otherwise, the move accuracy is calculated using a formula that takes into account the difference in win percentages.
        The formula is: raw = 103.1668100711649 * exp(-0.04354415386753951 * win_diff) - 3.166924740191411
        The move accuracy is then adjusted to be between 0 and 100, with an additional 1% uncertainty bonus.

    Example:
        eval_old = -0.5
        eval = 0.2
        side_to_move = 1
        move_accuracy(eval_old, eval, side_to_move)
        Output: 95.678

    """
    # takes into account side to move
    w_old = winpercent(eval_old,side_to_move) 
    w_new = winpercent(eval,side_to_move)

    # accuracy percent
    if w_new > w_old:
        return 100.
    else:
        win_diff = w_old - w_new
        raw = 103.1668100711649 * np.exp(-0.04354415386753951*win_diff) -3.166924740191411
        return min(100,max(0,raw+1)) # + 1  uncertainty bonus (due to imperfect analysis)
    
def game_selector(game):
    """
    Determines whether a chess game meets certain criteria for selection.

    Args:
        game (chess.pgn.Game): The game object containing information about the chess game.

    Returns:
        bool: True if the game meets all the criteria and should be selected, False otherwise.
    """
    event = game.headers.get("Event", "")
    result = game.headers.get("Result", "")
    white_elo = int(game.headers.get("WhiteElo", 0))
    black_elo = int(game.headers.get("BlackElo", 0))
    termination = game.headers.get("Termination", "")

    return (
        event == "Rated Rapid game"
        and termination == "Normal"
        and result in ["0-1", "1-0"]
        and 1700 < white_elo < 2000
        and 1700 < black_elo < 2000
        and first_evaluation(game) is not None
    )

def filter_and_write_to_pgn(input_pgn_path, output_pgn_path, condition_func):
    """
    Filter and write chess games to a PGN file based on a given condition.

    Args:
        input_pgn_path (str): The file path of the input PGN file containing the chess games.
        output_pgn_path (str): The file path of the output PGN file to write the filtered games.
        condition_func (function): A function that takes a chess game object as input and returns a boolean value indicating whether the game meets certain criteria for selection.

    Returns:
        None

    Raises:
        FileNotFoundError: If the input PGN file does not exist.

    Example:
        filter_and_write_to_pgn("input.pgn", "output.pgn", game_selector)

    Note:
        The condition_func should be a function that takes a chess.pgn.Game object as input and returns True if the game meets the criteria and should be selected, False otherwise.
    """
    filtered_games = []
    iall = 0
    ievl = 0

    with open(input_pgn_path) as pgn_file:
        while ievl<total_games:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                break  # No more games in the file
            
            # increment counter
            iall += 1

            # Apply your condition to filter games
            if condition_func(game):
                ievl += 1
                filtered_games.append(game)
                print(iall,ievl)

            # print status
            #if ievl % 1000 == 0:
            #    print(iall,ievl)

    # Write the filtered games to the output PGN file
    with open(output_pgn_path, 'w') as output_file:
        for game in filtered_games:
            output_file.write(str(game) + '\n\n')

if __name__ == "__main__":
    # read the file path of the game database
    with open(input_file,'r') as infile:
        input_pgn_path = json.load(infile)

    filter_and_write_to_pgn(input_pgn_path, output_pgn_path, game_selector)