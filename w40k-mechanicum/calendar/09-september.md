# Cult Mechanicus Liturgical Calendar - September

## September 1 - Feast of the Least Squares

**Purpose** - Remembering what linear regression minimises.

**Context** - Linear regression fits the line that makes the sum of squared vertical distances smallest. Because the distances are squared, one point far from the rest pulls the line hard. The tech-priests inspect such points before they trust the line.

## September 2 - Vigil of the Unrepeatable Run

**Purpose** - Expecting small differences between runs with fixed seeds.

**Context** - Fixed seeds do not make every GPU operation deterministic. Some operations give slightly different results from run to run. PyTorch can be told to use deterministic algorithms only, at a cost in speed. Otherwise expect small differences and, like the enginseers, report the results of several runs.

## September 3 - Observance of the Lost Degree

**Purpose** - Knowing which variance formula a tool computes.

**Context** - The sample variance divides by n minus 1, because the mean was estimated from the same data. NumPy divides by n by default; pandas divides by n minus 1. The Magos asks which one you computed.

## September 4 - Vigil of the Straight Line

**Purpose** - Plotting the data before trusting a correlation.

**Context** - The correlation coefficient measures linear association only. A perfect U-shaped dependence can give a coefficient of zero. Look at the scatter plot before you trust the number. The Magos wants the plot beside the coefficient.

## September 5 - Commemoration of Saint Marginia the Wide

**Purpose** - Honouring the widest margin between two classes.

**Context** - Marginia always drew the boundary with the widest margin between the classes. A support vector machine does the same, and only the points on the margin, the support vectors, decide where the boundary lies. The adepts honour her with every wide margin.

## September 6 - Feast of the Cross-Entropy

**Purpose** - Understanding why cross-entropy punishes confident wrong answers.

**Context** - Cross-entropy loss is the negative logarithm of the probability the model gave to the correct class. A confident wrong answer costs far more than a hesitant one. The machine spirit learns humility from this loss.

## September 7 - Rite of the Left Padding

**Purpose** - Padding prompts on the left for batched generation.

**Context** - For batched generation with a decoder-only language model, pad the shorter prompts on the left. With padding on the right the model must continue after the padding tokens, and its output degrades. Set the padding side of the tokeniser to left. The acolytes do.

## September 8 - Observance of the Area Beneath

**Purpose** - Reading the area under the ROC curve correctly.

**Context** - The area under the ROC curve is the probability that a randomly chosen positive example receives a higher score than a randomly chosen negative example. An area of 0.5 is the result of random guessing, and no threshold is involved. The acolytes learn this early.

## September 9 - Vigil of the Extended Line

**Purpose** - Distrusting predictions outside the training range.

**Context** - A model is supported by data only inside the range of inputs it was trained on. Outside that range nothing constrains its predictions, and it gives them with the same confidence. The Magos calls such confidence a heresy.

## September 10 - Feast of the Narrow Waist

**Purpose** - Learning a compressed representation with an autoencoder.

**Context** - An autoencoder squeezes its input through a narrow middle layer and rebuilds it on the other side, so it must learn a compressed representation. Inputs it rebuilds badly are unlike its training data. The servo-skulls report those inputs.

## September 11 - Rite of the Tracked Run

**Purpose** - Recording every experiment run in MLflow.

**Context** - An experiment tracker records the parameters, metrics and output files of every run. MLflow is installed on the workstation. A run recorded there needs no file name such as final_v3. The tech-priests call that name a small heresy.

## September 12 - Observance of the Naive Assumption

**Purpose** - Knowing what Naive Bayes assumes.

**Context** - Naive Bayes assumes that the features are independent given the class. That is rarely true, yet the classifier often ranks the examples well. Its probabilities, however, are overconfident. The tech-priests call the classifier naive but useful.

## September 13 - Feast of the Full Byte

**Purpose** - Counting the 256 values of one byte.

**Context** - Day 256 of a common year is September 13. In a leap year day 256 falls one day earlier. 256 is 2 to the power 8, the number of values one byte can hold, 0 to 255. The cogitator stores every byte in this range.

## September 14 - Commemoration of Saint Lensa the Straightener

**Purpose** - Remembering the saint who corrected lens distortion.

**Context** - A lens bends straight lines, most at the edges of the image. Lensa photographed a checkerboard from many angles to estimate the camera matrix and the distortion coefficients. She corrected every image before she measured anything in it. The tech-priests do the same.

## September 15 - Rite of the Masked Token

**Purpose** - Training a model to predict hidden words.

**Context** - In masked language modelling some tokens of a text are hidden, and the model learns to predict them from the words on both sides. The text supplies its own labels, so no human annotator is needed. The servitors do the hiding.

## September 16 - Vigil of the Three Doors

**Purpose** - Testing intuition against a famous puzzle of probability.

**Context** - There are three doors and one prize. An adept picks a door. The Magos, who knows where the prize is, opens an empty door of the other two. Switching wins two times in three. An adept who doubts it should simulate it on the cogitator.

## September 17 - Observance of the Two Averages

**Purpose** - Saying which average a report uses.

**Context** - The macro average is the mean of the per-class scores, and every class counts equally. The micro average pools all examples, so large classes dominate. Say which one you report. The Magos asks this first.

## September 18 - Feast of the Denoising Step

**Purpose** - Generating images by removing noise step by step.

**Context** - A diffusion model is trained to remove a little noise from a noised image. To generate, it starts from pure noise and removes noise step by step until an image remains. The machine spirit finds the picture in the noise.

## September 19 - Rite of the Weighed Model

**Purpose** - Computing the memory a model needs for its weights.

**Context** - Memory for weights is the number of parameters times the bytes per parameter. 7 billion parameters in 16-bit floats need 14 GB before any activations. Compute it before you choose a card. The enginseers do this calculation first.

## September 20 - Rite of the Pseudoinverse

**Purpose** - Solving more equations than unknowns by least squares.

**Context** - With more equations than unknowns there is usually no exact solution. The pseudoinverse gives the least-squares solution, the one with the smallest sum of squared errors. In NumPy the enginseers call lstsq and never build the pseudoinverse by hand.

## September 21 - Commemoration of Saint Activa the Inquirer

**Purpose** - Labelling only the examples the model is unsure of.

**Context** - Activa let the model point at the examples it was least sure of and sent only those to the annotators. That often reaches the same accuracy with far fewer labels than random choice. The acolytes call this active learning.

## September 22 - Vigil of the Misread Reward

**Purpose** - Watching what an agent does, not only its score.

**Context** - A reinforcement-learning agent maximises the reward as it was written, not as it was meant. An agent paid per point collected may circle one spot for ever and never finish the course. Watch the behaviour, not only the score. The machine spirit obeys the reward exactly as written.

## September 23 - Feast of the Three Sigmas

**Purpose** - Remembering the 68, 95 and 99.7 percent rule.

**Context** - In a normal distribution about 68 percent of values lie within one standard deviation of the mean. 95 percent lie within two and 99.7 percent within three. Heavy-tailed data have values outside three standard deviations far more often than this rule says. The Magos remembers all three numbers.

## September 24 - Rite of the Shown Working

**Purpose** - Asking a language model to reason step by step.

**Context** - Asking a language model to reason step by step before it answers often improves accuracy on problems of several steps. The reasoning it writes is not guaranteed to be how it reached the answer. The Magos wants the reasoning shown, but does not accept it as proof.

## September 25 - Feast of the U-Shaped Network

**Purpose** - Knowing the U-Net and its skip connections.

**Context** - A U-Net shrinks the image step by step in an encoder and enlarges it again in a decoder. Skip connections carry the fine detail from each encoder stage straight to the matching decoder stage. The tech-priests usually choose the U-Net for segmentation and for the denoiser of a diffusion model.

## September 26 - Vigil of the Tainted Normal

**Purpose** - Keeping anomalies out of the 'normal' training data.

**Context** - A detector trained on 'normal' data that contains anomalies learns those anomalies as normal. Clean the training set, or use a method that tolerates a stated share of contamination. The enginseers inspect the training set for anomalies first.

## September 27 - Observance of the Cast Shadow

**Purpose** - Seeing least squares as a projection.

**Context** - Projecting a vector onto a subspace gives the point of the subspace closest to it. Least squares is such a projection: the fitted values are the projection of the target onto the space spanned by the features. The residual is perpendicular to every feature. The adepts call the projection a shadow.

## September 28 - Commemoration of Saint Censora the Patient

**Purpose** - Treating an unfinished lifetime as at least the time observed.

**Context** - Censora kept the records of machines still running when the study ended. The lifetime of such a machine is at least the time observed in the study. Dropping these records, or counting the end of the study as a failure, makes lifetimes look shorter than they are. The adepts honour her.

## September 29 - Observance of the Geometric Mean

**Purpose** - Averaging growth factors with the geometric mean.

**Context** - Growth factors multiply, so their average is the geometric mean. A doubling followed by a halving returns to the start: the arithmetic mean of 2 and 0.5 is 1.25, the geometric mean is 1. Adepts use the geometric mean for growth.

## September 30 - Feast of the Cached Keys

**Purpose** - Knowing that the key-value cache takes GPU memory.

**Context** - During generation a transformer keeps the keys and values of the tokens it has already processed. So each new token is computed without redoing the past. The cache takes GPU memory that grows with the length of the context. The enginseers watch it in nvidia-smi.

