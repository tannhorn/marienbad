import chess
import chess.pgn
import re
import numpy as np
import json

white_pawn_moves = ['a2a3', 'a2a4', 'b2b3', 'b2b4', 'c2c3', 'c2c4', 'd2d3', 'd2d4',
                    'e2e3', 'e2e4', 'f2f3', 'f2f4', 'g2g3', 'g2g4', 'h2h3', 'h2h4',
                    'a3a4', 'b3b4', 'c3c4', 'd3d4', 'e3e4', 'f3f4', 'g3g4', 'h3h4',
                    'a4a5', 'b4b5', 'c4c5', 'd4d5', 'e4e5', 'f4f5', 'g4g5', 'h4h5',
                    'a5a6', 'b5b6', 'c5c6', 'd5d6', 'e5e6', 'f5f6', 'g5g6', 'h5h6',
                    'a6a7', 'b6b7', 'c6c7', 'd6d7', 'e6e7', 'f6f7', 'g6g7', 'h6h7',
                    'a7a8', 'b7b8', 'c7c8', 'd7d8', 'e7e8', 'f7f8', 'g7g8', 'h7h8']

black_pawn_moves = ['a7a6', 'a7a5', 'b7b6', 'b7b5', 'c7c6', 'c7c5', 'd7d6', 'd7d5',
                    'e7e6', 'e7e5', 'f7f6', 'f7f5', 'g7g6', 'g7g5', 'h7h6', 'h7h5',
                    'a6a5', 'b6b5', 'c6c5', 'd6d5', 'e6e5', 'f6f5', 'g6g5', 'h6h5',
                    'a5a4', 'b5b4', 'c5c4', 'd5d4', 'e5e4', 'f5f4', 'g5g4', 'h5h4',
                    'a4a3', 'b4b3', 'c4c3', 'd4d3', 'e4e3', 'f4f3', 'g4g3', 'h4h3',
                    'a3a2', 'b3b2', 'c3c2', 'd3d2', 'e3e2', 'f3f2', 'g3g2', 'h3h2',
                    'a2a1', 'b2b1', 'c2c1', 'd2d1', 'e2e1', 'f2f1', 'g2g1', 'h2h1']

starting_eval = str(0.3) # for consistency with the rest of evals

def parse_time_remaining(comment):
  print(comment)
  match = re.search(r"\[%clk\s(\d{1}:\d{2}:\d{2})\]", comment)
  if match:
    return match.group(1)
  return None

def parse_evaluation(comment):
  match = re.search(r"\[%eval\s(.+?)\]", comment)
  if match:
    return match.group(1)
  return None

def first_evaluation(game):
  if game.next() is not None:
    comment = game.next().comment
    return parse_evaluation(comment)
  return None

def is_pawn_move(board,move):
  moving_piece = board.piece_at(move.from_square)
  board.push(move)
  return moving_piece.piece_type == chess.PAWN

# based on:
# https://lichess.org/page/accuracy
# https://github.com/lichess-org/lila/pull/11128
# https://github.com/lichess-org/lila/blob/master/modules/analyse/src/main/WinPercent.scala#L23
# https://github.com/lichess-org/lila/blob/master/modules/analyse/src/main/AccuracyPercent.scala#L38-L44
def winpercent(eval,side_to_move):
  rescaled_stm = 2*side_to_move-1
  if eval[0] == '#':
    mate_in = int(eval[1:])
    if mate_in*rescaled_stm > 0:
      return 100.
    else:
      return -100.
  else:
    return 50. + 50. * (2./(1. + np.exp(-0.00368208e2*rescaled_stm*float(eval))) - 1.)

def move_accuracy(eval_old,eval,side_to_move):
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

def play_through_game(game):
  board = chess.Board()
  eval = starting_eval

  # iterate through each node and move in the game
  for node,move in zip(game.mainline(),game.mainline_moves()):
      # store old and get the current eval
      eval_old = eval
      eval = parse_evaluation(node.comment)

      # skip without eval, this should happen only for the final move
      if eval is None:
        continue

      # get side to move
      side_to_move = board.turn

      # get the current move number
      move_number = board.fullmove_number

      # convert to move accuracy
      accuracy = move_accuracy(eval_old,eval,side_to_move)

      # print
      # note that is_pawn_move also pushes the move on the board
      if is_pawn_move(board,move):
        print(move_number,side_to_move,move.uci()[:4],accuracy)
      #exit()
    
  return

if __name__ == "__main__":
  # read the file path of the game database
  input_file = "data_path.json"
  with open(input_file,'r') as infile:
    file_path = json.load(infile)

  # start pgn read
  pgn = open(file_path)

  # first game
  game = chess.pgn.read_game(pgn)
  iall = 0
  ievl = 0

  # while loop to evaluate
  while game is not None:
    # increment counter
    iall += 1
    # check if game was analysed
    if first_evaluation(game) is not None:
      ievl +=1
      # play through the game
      play_through_game(game)

    # print status
    print(iall,ievl)

    # proceed to read next game
    game = chess.pgn.read_game(pgn)
