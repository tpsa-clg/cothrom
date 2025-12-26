#ifndef STATFUNCS_H
#define STATFUNCS_H

#include <vector>
using std::vector;

// Integrated autocorrelation time estimator & corresponding error of a Markov chain.
void autocorr(const vector<double>& chain, double& tau_hat, double& tau_hat_err, const double& mean, const double& quadratic_sum);
// Return an effectively independent subset of an autocorrelated Markov chain.
vector<double> thin(const vector<double>& chain, const int& tau);

// Sample mean, sample variance, and integrated autocorrelation time estimator, and their corresponding errors, of a Markov chain.
void Markov_chain_calculations(const vector<double>& chain, vector<double>& means, vector<double>& mean_errs, vector<double>& vars, vector<double>& var_errs, vector<double>& taus, vector<double>& tau_errs);

#endif
