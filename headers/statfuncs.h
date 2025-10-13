#ifndef STATFUNCS_H
#define STATFUNCS_H

#include <vector>
using std::vector;

// Return the mean of a vector.
double mean(const vector<double>& chain);
// Return the sum of squared distances from the mean of a vector.
double quad_sum(const vector<double>& chain, const double& mu);
// Return the standard error in the mean of a vector.
double mean_error(const vector<double>& chain, const double& mu);

// Integrated autocorrelation time & corresponding error of a Markov chain.
void autocorr(const vector<double>& chain, const double& mu, double& tau, double& deltatau);
// Return an effectively independent subset of an autocorrelated Markov chain.
vector<double> thin(const vector<double>& chain, const int& tau);

#endif
