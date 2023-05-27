import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import chess
import chess.pgn

# -- load the data
input_file = "pawn_moves_small.json"
with open(input_file,'r') as infile:
  data = json.load(infile)

# -- select color and other custom selection
color = 'white'
if color == 'white':
  starting_rank = 6
else:
  starting_rank = 1 # rank number is flipped!

move_number_range = (1,1)

# -- synthetise data
results = {key: None for key in data[color]['acc']}
for key in results:
  indices = [move_number_range[0] <= n <= move_number_range[1] for n in data[color]['num'][key]]
  temp = [element for element, boolean in zip(data[color]['acc'][key], indices) if boolean]
  if len(temp)>0:
    results[key] = sum(temp)/len(temp)
  else:
    results[key] = np.nan

# -- plotting the chess board
blackval = 0.9
whiteval = 1.
value_min = 0.
value_max = 1.

brdplot = np.array([[whiteval,blackval,whiteval,blackval,whiteval,blackval,whiteval,blackval],
                    [blackval,whiteval,blackval,whiteval,blackval,whiteval,blackval,whiteval],
                    [whiteval,blackval,whiteval,blackval,whiteval,blackval,whiteval,blackval],
                    [blackval,whiteval,blackval,whiteval,blackval,whiteval,blackval,whiteval],
                    [whiteval,blackval,whiteval,blackval,whiteval,blackval,whiteval,blackval],
                    [blackval,whiteval,blackval,whiteval,blackval,whiteval,blackval,whiteval],
                    [whiteval,blackval,whiteval,blackval,whiteval,blackval,whiteval,blackval],
                    [blackval,whiteval,blackval,whiteval,blackval,whiteval,blackval,whiteval]])

fig,ax = plt.subplots(figsize=[10,10])
plt.imshow(brdplot, cmap="gray",vmin=value_min,vmax=value_max)

# -- set the borders to a given color
ax.tick_params(color=str(blackval), labelcolor=str(blackval))
for spine in ax.spines.values():
  spine.set_edgecolor(str(blackval))

# -- add rank and file labels
# rank labels on the left side
for i in range(8):
  ax.text(-1, i, str(8 - i), ha='center', va='center', fontsize=14)

# file labels on the top
for j in range(8):
  ax.text(j, -1, chr(97 + j), ha='center', va='center', fontsize=14)

plt.xticks([])
plt.yticks([])

# -- we will need some colors for prettier visualisation
cmap = 'magma_r'
norm = matplotlib.colors.Normalize(vmin=75, vmax=100) 
sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)

# -- write results
digits = 1
for key in results:
  move = chess.Move.from_uci(key)
  fr_sq_x = chess.square_file(chess.square_mirror(move.from_square))
  fr_sq_y = chess.square_rank(chess.square_mirror(move.from_square))
  to_sq_x = chess.square_file(chess.square_mirror(move.to_square))
  to_sq_y = chess.square_rank(chess.square_mirror(move.to_square))
  print(move,fr_sq_x,fr_sq_y,results[key])
  #exit()
  if fr_sq_y == starting_rank:
    if abs(to_sq_y-fr_sq_y)<2:
      # the sign is again inverted here!
      fr_sq_y = fr_sq_y+0.3
    else:
      fr_sq_y = fr_sq_y-0.3
  ax.text(fr_sq_x,fr_sq_y, format(results[key], f".{digits}f"), ha='center', va='center', fontsize=14,color=sm.to_rgba(results[key]))

plt.show()