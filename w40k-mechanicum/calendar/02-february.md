# Cult Mechanicus Liturgical Calendar - February

## February 1 - Feast of the Regularised Weight

**Purpose** - Using weight decay to keep model weights small.

**Context** - Weight decay asks every parameter to justify its size. With a little of it the weights stay small, the function stays smooth and the validation loss stays honest. The Magos adds it as a matter of habit.

## February 2 - Rite of the Two-by-Two Table

**Purpose** - Counting the four cells behind accuracy, precision and recall.

**Context** - Draw the two-by-two table: true positives, false positives, false negatives and true negatives. Accuracy, precision, recall and F1 are all counted from those four cells. The tech-priests draw it before they trust any single score.

## February 3 - Vigil of the Exhausted Memory

**Purpose** - Dealing with 'CUDA out of memory'.

**Context** - 'CUDA out of memory' means the card has no more memory to give, and no litany will change that. Halve the batch, shorten the sequences or switch to mixed precision. Only then ask the Magos for a bigger GPU.

## February 4 - Feast of the Scree Plot

**Purpose** - Choosing how many principal components to keep.

**Context** - A scree plot shows the variance explained by each principal component, largest first. Keep the components before the curve flattens (the elbow), or enough of them to reach a stated share of the variance, such as 95 percent. The acolytes read the elbow first.

## February 5 - Commemoration of Saint Strata the Even-Handed

**Purpose** - Remembering the saint who kept class proportions in every fold.

**Context** - Saint Strata divided the data so that every fold held the rare class in the same proportion as the whole. In her memory the tech-priests stratify their splits. Without it, one fold may contain no positive examples at all.

## February 6 - Feast of the Warm-Up

**Purpose** - Raising the learning rate gently over the first steps.

**Context** - Do not start training at the full learning rate. Raise it gently over the first steps, while the running statistics of the optimiser are still unreliable. Only then let it reach full strength. The enginseers never start a cold forge at full power.

## February 7 - Rite of the Natural Base

**Purpose** - Remembering that e is the base of the natural logarithm.

**Context** - Second month, seventh day: 2.7, the first digits of e. It is usually the base of the logarithm in your cross-entropy loss, and of the exponential in every softmax. The acolytes learn this number by heart.

## February 8 - Observance of the Sampling Bias

**Purpose** - Asking who or what is missing from your sample.

**Context** - The data you could collect is not the data that exists. Ask today who or what never reached the table. A model inherits every blind spot of its sample. The Magos asks this question before every analysis.

## February 9 - Feast of the Surrogate Model

**Purpose** - Searching hyperparameters with a cheap surrogate model.

**Context** - Bayesian optimisation of hyperparameters fits a cheap model, the surrogate, to the scores of the trials run so far. The surrogate predicts the score of untried settings and how uncertain that is, and the next trial is chosen from it. It pays off when each trial is expensive, as the tech-priests know.

## February 10 - Feast of the Falling Loss

**Purpose** - Reading training and validation loss on the same plot.

**Context** - Plot the training and validation loss on the same axes. If both fall together, the model is learning well. If the training loss falls while the validation loss climbs, that is the first sign of overfitting. A tech-priest reads both curves before any other result.

## February 11 - Rite of the Many Hypotheses

**Purpose** - Correcting the threshold when you run many tests.

**Context** - Test twenty true null hypotheses at the 5 percent level and you expect one false discovery. Count how many comparisons you ran today. Correct the threshold before you announce a result. The Magos calls a discovery found by chance tech-heresy.

## February 12 - Rite of the Ranked Pair

**Purpose** - Using rank correlation for relations that only rise or fall.

**Context** - Rank correlation (Spearman's coefficient) is the ordinary correlation computed on the ranks of the values. It detects any relation that only rises or only falls, straight or curved. One extreme value moves it little. The adepts rank the pair before they judge it.

## February 13 - Commemoration of Saint Calibra the Well-Tempered

**Purpose** - Remembering the saint whose 70 percent meant seven in ten.

**Context** - Of all the times Saint Calibra's model said 70 percent, it was right seven times in ten. In her memory the tech-priests check their own models with a reliability plot. Accuracy and calibration are different things.

## February 14 - Feast of the Sharpened Prompt

**Purpose** - Writing a prompt as a clear brief to the model.

**Context** - Tell the model who the reader is, what the output is for and what a good answer looks like. A prompt written as a clear brief to a capable colleague usually works better than any magic words. The machine spirit cannot guess what you did not say.

## February 15 - Vigil of the Shared Vault

**Purpose** - Sharing data once through the shared volume.

**Context** - Every user can read what is in @volumes/shared. Put a dataset there once instead of copying it ten times, and never leave a secret there. The tech-priests keep private files in @volumes/personal.

## February 16 - Observance of the Expected Calibration Error

**Purpose** - Measuring calibration with the expected calibration error.

**Context** - Sort the predictions into bins by confidence. In each bin compare the average confidence with the share of correct answers. The expected calibration error is the average gap, weighted by bin size. It depends on the number of bins, so state it. The Magos will ask.

## February 17 - Observance of the Unseen Class

**Purpose** - Distrusting accuracy on imbalanced data.

**Context** - When one case in a hundred is positive, a model that always answers 'no' scores 99 percent accuracy and finds nothing. On imbalanced data, use precision, recall and the precision-recall curve instead. The tech-priests do not trust accuracy alone here.

## February 18 - Feast of the Half-Precision Float

**Purpose** - Using mixed precision and keeping the gradient scaler on.

**Context** - Mixed precision runs most operations in 16-bit floats and keeps the sensitive ones in 32-bit. Memory use falls and speed rises, a blessing for any card. Leave the gradient scaler on, or small gradients can underflow to zero.

## February 19 - Commemoration of Saint Epsilona the Noise-Bearer

**Purpose** - Remembering the saint of the reparametrisation trick.

**Context** - A gradient cannot pass through a random draw. Epsilona's reparametrisation trick wrote the sample as the mean plus the standard deviation times standard normal noise. The randomness sits in the noise alone, so the gradient reaches the mean and the standard deviation. The tech-priests use it in her memory.

## February 20 - Vigil of the Early Stop

**Purpose** - Stopping training when the validation loss stops improving.

**Context** - Watch the validation loss. When it has not improved for a set number of epochs, stop the run and restore the best checkpoint. More training would only fit the noise. An adept who stops in time saves GPU hours.

## February 21 - Rite of the Prior and the Posterior

**Purpose** - Knowing when the prior or the data has more weight.

**Context** - State what you believed before the data, then let the evidence update it. With little data the prior has more weight in the posterior. With much data the evidence has more. Know which case you are in, as every Bayesian tech-priest does.

## February 22 - Observance of the Removed Part

**Purpose** - Removing one component at a time to test its value.

**Context** - An ablation removes one component at a time and measures again. If the score does not fall, that part adds nothing. The table then shows the Magos which of your additions earn their place.

## February 23 - Feast of the Unturned Vector

**Purpose** - Honouring eigenvectors and eigenvalues.

**Context** - An eigenvector of a matrix is a vector that the matrix only stretches and does not turn; the eigenvalue is the stretch factor. The eigenvectors of a covariance matrix are the principal components of the data. The tech-priests honour the vector that keeps its direction.

## February 24 - Feast of the Overlapping Boxes

**Purpose** - Measuring a detection with intersection over union.

**Context** - Intersection over union compares a predicted box with the true box: the area they share divided by the area they cover together. 1 is a perfect match. A detection is commonly counted as correct at 0.5 or more. The servitors compute it for every box.

## February 25 - Vigil of the Context Window

**Purpose** - Measuring prompts in tokens, not in characters.

**Context** - The model attends only to what fits inside its context window. Whatever falls outside does not exist for it. Tonight, measure your prompt in tokens, not in characters. The machine spirit reads nothing it cannot hold.

## February 26 - Observance of the Curse of Dimensions

**Purpose** - Remembering that data grows sparse in high dimensions.

**Context** - As dimensions multiply, the data grows sparse and every point drifts far from every other. A method that relies on nearest neighbours in three dimensions may find no near neighbours at all in three thousand. The enginseers call this a curse.

## February 27 - Commemoration of Saint Tempera the Cool-Headed

**Purpose** - Remembering the saint who tamed an overconfident network.

**Context** - Tempera used temperature scaling: she divided the logits of an overconfident network by one number, the temperature, fitted on held-out data. A temperature above 1 softens the probabilities. The predicted class does not change, so the accuracy stays the same. The tech-priests do likewise in her memory.

## February 28 - Feast of the Isolated Point

**Purpose** - Understanding how an isolation forest finds anomalies.

**Context** - An isolation forest cuts the data with random splits. An anomaly sits apart, so few splits isolate it, while a normal point needs many. A short path to isolation means a likely anomaly. The cogitator counts the cuts for every point.

## February 29 - Observance of the Intercalary Day

**Purpose** - Testing date code on 29 February.

**Context** - This day exists only in leap years. Code that assumes 365 days or a 28-day February fails on it. Never do calendar arithmetic by hand: use a date library, and test it on 29 February. The Magos calls hand-made date arithmetic tech-heresy.

