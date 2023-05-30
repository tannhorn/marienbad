import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import chess
import chess.pgn

# -- load the data
input_file = "pawn_moves.json"
with open(input_file,'r') as infile:
  data = json.load(infile)

# -- select color and other custom selection
color = 'white'
if color == 'white':
  starting_rank = 6
  starting_rank_correction = 0.25
else:
  starting_rank = 1 # rank number is flipped!
  starting_rank_correction = -0.25

move_number_range = (1,1e5)

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
blackval = 0.95
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
# rank labels on the left side and the right side
for i in range(8):
  ax.text(-1, i, str(8 - i), ha='center', va='center', fontsize=14)
  ax.text(8, i, str(8 - i), ha='center', va='center', fontsize=14)

# file labels on the top and bottom
for j in range(8):
  ax.text(j, -1, chr(97 + j), ha='center', va='center', fontsize=14)
  ax.text(j, 8, chr(97 + j), ha='center', va='center', fontsize=14)

plt.xticks([])
plt.yticks([])

# -- we will need some colors for prettier visualisation
cmap = 'magma_r'
cmap_r = 'magma'
norm = matplotlib.colors.Normalize(vmin=75, vmax=100) 
sm = matplotlib.cm.ScalarMappable(cmap=cmap, norm=norm)
sm_r = matplotlib.cm.ScalarMappable(cmap=cmap_r, norm=norm)

# -- write results
digits = 1
for key in results:
  move = chess.Move.from_uci(key)
  fr_sq_x = chess.square_file(chess.square_mirror(move.from_square))
  fr_sq_y = chess.square_rank(chess.square_mirror(move.from_square))
  to_sq_x = chess.square_file(chess.square_mirror(move.to_square))
  to_sq_y = chess.square_rank(chess.square_mirror(move.to_square))

  rect_x = fr_sq_x-0.5
  rect_y = fr_sq_y-0.5
  rect_xl = 1.
  rect_yl = 1.

  if fr_sq_y == starting_rank:
    if abs(to_sq_y-fr_sq_y)<2:
      # the sign is again inverted here!
      rect_y = fr_sq_y
      rect_yl = 0.5
      fr_sq_y = fr_sq_y+starting_rank_correction
    else:
      rect_yl = 0.5
      fr_sq_y = fr_sq_y-starting_rank_correction
   
  if results[key] is not np.nan:
    rect = matplotlib.patches.Rectangle((rect_x,rect_y), rect_xl, rect_yl, color='none', fc=sm.to_rgba(results[key]),alpha=0.5)
    ax.add_patch(rect)
    ax.text(fr_sq_x,fr_sq_y, format(results[key], f".{digits}f"), ha='center', va='center', fontsize=14,color=sm_r.to_rgba(results[key]))

plt.show()