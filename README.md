# Marienbad

In this repository, I store code created during my effort to get better at working with data...and perhaps it will help me to learn something about chess, too.

## Pawn move evaluation

There is content in the folder **pawn_move_evaluation**: the Python code therein processeses game data from the [Lichess database](https://database.lichess.org/) in order to assess the average accuracy of a given pawn move and subsequently plots it. The data is loaded from the **data** folder (which is entry in this Git repository). The results of this analysis has been discussed in a [Lichess blog post](https://lichess.org/@/A_Bohemian/blog/f-is-for-forget-about-it-/wFYtjn86).

## Win prediction

I have also started looking into the possibility of predicting the winner of a game just based on the given board state with the use of deep learning in the folder **win_predictor**. Same Lichess database is used.
