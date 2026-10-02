# Cult Mechanicus Liturgical Calendar - May

## May 1 - Feast of the Chain Rule

**Purpose** - Remembering how backpropagation works.

**Context** - Backpropagation is the chain rule of calculus applied from the loss back to the first layer. It reuses each intermediate result on the way. Every network trained by gradient descent rests on this one rule, and the tech-priests honour it.

## May 2 - Rite of the Shuffled Deck

**Purpose** - Shuffling the training data every epoch.

**Context** - Shuffle the training data again at the start of each epoch. Batches in a fixed order, or sorted by label, give the optimiser a biased sequence of gradients. The model then learns worse. The acolytes shuffle before every epoch.

## May 3 - Observance of the Base Rate

**Purpose** - Asking how common a condition is before trusting a test.

**Context** - A test that is 99 percent accurate, used on a condition found in one case per ten thousand, gives mostly false alarms. Always ask how common the thing was before the evidence arrived. The Magos asks this question first.

## May 4 - Feast of the Brier Score

**Purpose** - Scoring probabilities with the Brier score.

**Context** - The Brier score is the mean squared difference between the predicted probability and the outcome, 0 or 1. Lower is better, and a forecast of 0.5 for everything scores 0.25. The score rewards probabilities that are both calibrated and decisive. The enginseers judge every forecast by it.

## May 5 - Feast of the Five Folds

**Purpose** - Cross-validating with five folds.

**Context** - Fifth day of the fifth month, so five folds. Train five times, each time holding out a different fifth of the data. Report the mean and the spread of the five scores, not only the best one. The adepts report all five.

## May 6 - Commemoration of Saint Isotropa the Even-Spread

**Purpose** - Remembering the saint who doubted a raw cosine similarity.

**Context** - Isotropa noticed that the embeddings of a language model often fill only a narrow cone of the space. Any two of them then have a high cosine similarity. She compared similarities with each other, or centred the embeddings first. In her memory the tech-priests never read a raw cosine of 0.8 as 'very similar'.

## May 7 - Rite of the Lowered Temperature

**Purpose** - Lowering the temperature for precise answers.

**Context** - Temperature divides the logits before sampling. Below one, the model keeps to its likeliest tokens, and above one it picks less likely tokens more often. Keep the temperature low for extraction and code. The tech-priests raise it only for invention.

## May 8 - Observance of the Confounder

**Purpose** - Looking for the third variable behind a correlation.

**Context** - Ice-cream sales and sunburn rise together, but neither causes the other. The summer sun drives both. Before you claim that X moves Y, search for a third variable that moves them both. To skip that search is heresy.

## May 9 - Feast of the Decision Tree

**Purpose** - Limiting the depth of a decision tree.

**Context** - A tree asks one question at a time, so even a sceptical Magos can read it. Left unpruned, it grows a leaf for every training row. Limit its depth, or combine it with other trees into an ensemble.

## May 10 - Rite of the Pruned Trial

**Purpose** - Pruning poor hyperparameter settings early with successive halving.

**Context** - Most hyperparameter settings show early that they are poor. Successive halving gives many settings a small budget, keeps the best fraction and gives those more, again and again. Far more settings are tried for the same total compute, which the tech-priests count as thrift.

## May 11 - Observance of the Three Norms

**Purpose** - Naming which norm a distance or a clip uses.

**Context** - The L2 norm of a vector is its straight-line length. The L1 norm is the sum of the absolute values of its components. The maximum norm is its largest absolute component. The Magos asks which norm your 'distance' or 'clip' uses.

## May 12 - Observance of the Proxy Metric

**Purpose** - Checking that a metric still measures the real goal.

**Context** - Optimise a number hard enough and it stops measuring what it measured before. Ask today whether your metric still tracks the outcome that matters, or has become the goal itself. The Magos asks this of every metric.

## May 13 - Commemoration of Saint Seasona the Expectant

**Purpose** - Remembering the saint who removed the seasonal pattern before looking for anomalies.

**Context** - In a series with a daily or weekly cycle, the peaks are normal. Saint Seasona removed the trend and the seasonal pattern first and looked for anomalies in what remained. Without that step every Monday morning peak raises an alert. The enginseers do the same in her memory.

## May 14 - Feast of the Fine-Tuned Spirit

**Purpose** - Fine-tuning a pretrained model on your own task.

**Context** - A pretrained model already knows edges, grammar and much about the world. Fine-tuning asks it to learn only your task. This is why a few thousand examples can be enough to teach the machine spirit.

## May 15 - Rite of the Histogram

**Purpose** - Drawing a histogram of every numeric column.

**Context** - A histogram shows what the mean and the standard deviation hide: two peaks, a long tail, a spike at zero. Draw one for every numeric column. Try more than one bin width. Adepts look before they calculate.

## May 16 - Vigil of the Label Noise

**Purpose** - Looking for wrong labels in the dataset.

**Context** - Some labels in almost every dataset are simply wrong. Look at the examples where a good model disagrees most confidently with their labels. Many of them are errors in the data, not in the model. Send an acolyte to review them.

## May 17 - Observance of the Floating Point

**Purpose** - Remembering that floating-point numbers are not exact.

**Context** - The cogitator cannot store one tenth exactly in binary, so 0.1 plus 0.2 is not equal to 0.3. Compare floats within a tolerance, never with strict equality. The tech-priests count money as integers of its smallest unit.

## May 18 - Rite of the Expected Count

**Purpose** - Checking expected counts before a chi-squared test.

**Context** - The chi-squared test of independence compares the counts observed in a table with the counts expected if the two variables were unrelated. It is unreliable when expected counts are small; a common rule asks for at least 5 in each cell. The tech-priests check every cell first.

## May 19 - Rite of the Decoupled Decay

**Purpose** - Using AdamW when you want weight decay with Adam.

**Context** - In the Adam optimiser an L2 penalty added to the loss is rescaled by the adaptive step and no longer acts as weight decay. AdamW applies the decay to the weights directly, separately from the gradient. The tech-priests use AdamW when they want weight decay with Adam.

## May 20 - Memorial of Saint Normalia the Steady

**Purpose** - Remembering the saint of normalised layers.

**Context** - Saint Normalia rescaled the activations inside her network, so each layer received inputs of steady mean and variance. Training became faster and much less sensitive to the starting weights. The tech-priests normalise layers in her memory.

## May 21 - Observance of the Percentage Point

**Purpose** - Telling percentage points from percentages.

**Context** - A rise from 10 percent to 12 percent is two percentage points. It is also a 20 percent relative increase. Say which one you mean, because the two sound very different. The Magos distrusts a number without its unit.

## May 22 - Vigil of the Prompt Injection

**Purpose** - Treating retrieved text as data, not as commands.

**Context** - Text fetched from a web page or a document may carry instructions aimed at your model. Treat everything retrieved as data, never as a command. Give an agent no more authority than its task needs. Obeying such text is tech-heresy.

## May 23 - Feast of the Learning Curve

**Purpose** - Plotting a learning curve before gathering more data.

**Context** - Train on a tenth, a quarter, a half and all of your data. Plot the validation score against the size. If the curve still climbs, gather more data. If it has flattened, change the model, as the enginseers advise.

## May 24 - Rite of the Whitened Data

**Purpose** - Scaling decorrelated features to unit variance by whitening.

**Context** - PCA rotates the data so that the new features are uncorrelated. Whitening goes one step further and scales each of them to unit variance. Some methods learn more easily from whitened inputs. The tech-priests whiten the data for those methods.

## May 25 - Observance of the Target in Disguise

**Purpose** - Checking when each feature value becomes known.

**Context** - For each column, ask when its value is really known. A feature recorded after the outcome, or computed from it, predicts very well in training. It does not exist when the model is used. The Magos rejects such a feature.

## May 26 - Feast of the Gradient Boost

**Purpose** - Trying gradient boosting on tabular data.

**Context** - Each new tree in a boosted ensemble is fitted to the errors that the previous trees left behind. On tabular data gradient boosting remains a strong baseline. Try it before you build a deep neural network, as the acolytes learn to do.

## May 27 - Rite of the Causal Mask

**Purpose** - Understanding why a decoder cannot see later tokens.

**Context** - In a decoder-only transformer a causal mask lets each token attend only to the tokens before it. The model can then be trained on every position of a text in one pass, each position predicting its next token, without seeing the answer. The machine spirit is never shown the future.

## May 28 - Commemoration of Saint Tessella the Tiler

**Purpose** - Remembering the saint who cut large images into tiles.

**Context** - Shrinking a large image to the input size of the network can erase small objects: a defect ten pixels wide becomes one pixel. Saint Tessella cut the image into overlapping tiles and ran the detector on each tile at full resolution. The enginseers tile large images in her memory.

## May 29 - Feast of the Orthogonal Turn

**Purpose** - Remembering what an orthogonal matrix keeps unchanged.

**Context** - An orthogonal matrix turns or mirrors vectors without changing their lengths or the angles between them. Its inverse is its transpose. Because it keeps lengths, it neither shrinks nor inflates a signal that passes through it. The tech-priests call such a turn pure.

## May 30 - Observance of the Heavy Tail

**Purpose** - Handling data with a heavy tail.

**Context** - In some data a single observation outweighs a thousand ordinary ones: incomes, file sizes, city populations. There the mean is unstable and a larger sample can still surprise you. Use medians and quantiles there, as the Magos advises.

## May 31 - Feast of the Echoing Series

**Purpose** - Finding cycles with autocorrelation before forecasting.

**Context** - Autocorrelation is the correlation of a series with a copy of itself shifted by some lag. In daily data a peak at lag 7 shows a weekly cycle. Plot the autocorrelation before choosing a forecasting model. The servo-skulls listen for the echo of the week.
