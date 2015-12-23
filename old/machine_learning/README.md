# SARbayes

### Machine Learning

Goal: Create a regression learner that 

  - [x] Simple tabulation
  - [ ] Neural networks
      - [x] Genetic algorithm
      - [x] Backpropgation
  - [ ] Simulated annealing

##### Neural Networks

Transfer function: 

$$
t = b + \sum_{i}^{n} w_i x_i
$$

Activation function: 

$$
S(t) = \frac{1}{1 + e^{-t}} \\
\lim_{t \to \infty} S(t) = 1 \\
\lim_{t \to -\infty} S(t) = 0
$$
