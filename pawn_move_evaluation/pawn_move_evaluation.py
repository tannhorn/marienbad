import chess
import chess.pgn
import re
import numpy as np
import json

import common

# input/output file
input_file = "data_path.json"
output_file = "pawn_moves.json"

# games to be extracted from
total_games = 1e6

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

def play_through_game(game,resdict):
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
      color = chess.COLOR_NAMES[side_to_move]

      # get the current move number
      move_number = board.fullmove_number

      # convert to move accuracy
      accuracy = move_accuracy(eval_old,eval,side_to_move)

      # print
      # note that is_pawn_move also pushes the move on the board
      if is_pawn_move(board,move):
        move_name = move.uci()[:4]
        if move_name in common.pawn_moves[color]:
          resdict[color]['acc'][move_name].append(accuracy)
          resdict[color]['num'][move_name].append(move_number)
    
  return

if __name__ == "__main__":
  # instantiate dictionaries of results
  resdict = {}
  resdict['white'] = {}
  resdict['black'] = {}
  resdict['white']['acc'] = {}
  resdict['white']['num'] = {}
  resdict['black']['acc'] = {}
  resdict['black']['num'] = {}

  for move in common.pawn_moves['white']:
    resdict['white']['acc'][move] = []
    resdict['white']['num'][move] = []

  for move in common.pawn_moves['black']:
    resdict['black']['acc'][move] = []
    resdict['black']['num'][move] = []

  # read the file path of the game database
  with open(input_file,'r') as infile:
    file_path = json.load(infile)

  # start pgn read
  pgn = open(file_path)

  # first game
  game = chess.pgn.read_game(pgn)
  iall = 0
  ievl = 0

  # while loop to evaluate
  while game is not None and ievl<total_games:
    # increment counter
    iall += 1
    # check if game was analysed
    if first_evaluation(game) is not None:
      ievl +=1
      # play through the game and append results
      play_through_game(game,resdict)

    # print status
    if ievl % 1000 == 0:
      print(iall,ievl)

    # proceed to read next game
    game = chess.pgn.read_game(pgn)

  # write results to json
  json_dump = json.dumps(resdict,indent=2)
  with open(output_file,'w') as outfile:
    outfile.write(json_dump)
  