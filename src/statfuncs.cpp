#include <math.h>
#include <numeric>
#include <stdexcept>
#include "statfuncs.h"

void autocorr(const vector<double>& chain, double& tau_hat, double& tau_hat_err, const double& mean, const double& quadratic_sum)
{
  // tau_hat: autocorrelation time estimator
  // tau_hat_err: error in autocorrelation time estimator
  // mean, quadratic_sum: mean and sum of squared differences from mean
  // estimator according to https://doi.org/10.1007/978-1-4899-0319-8_6 chap. 3

  int N = chain.size();
  if (N < 2) throw std::invalid_argument("chain must have multiple entries");
  if (quadratic_sum < 0.) throw std::invalid_argument("quadratic_sum must be positive");
  if (quadratic_sum == 0.)
  {
    tau_hat = 1.;
    tau_hat_err = 0.;
    return;
  }

  int M = 0;
  double fac = 2.*N/quadratic_sum;
  tau_hat = 1.;
  do
  {
    M++;
    double sum = 0.;
    #pragma omp parallel for reduction(+:sum)
    for (int n = 0; n < N-M; n ++) sum += (chain[n]-mean)*(chain[n+M]-mean);
    tau_hat += sum/(N-M)*fac;
  } while ((M < N-1) && (M < 5.*tau_hat || tau_hat <= 0.));
  if (M < N-1) tau_hat_err = tau_hat*sqrt((4.*M+2.)/N);
  else
  {
    tau_hat = nan("");
    tau_hat_err = nan("");
  }
}
vector<double> thin(const vector<double>& chain, const int& tau)
{
  vector<double> thinned(chain.size()/tau);
  #pragma omp parallel for
  for (int n = 0; n < thinned.size(); n ++) thinned[n] = chain[n*tau];
  return thinned;
}

void Markov_chain_calculations(const vector<double>& chain, vector<double>& means, vector<double>& mean_errs, vector<double>& vars, vector<double>& var_errs, vector<double>& taus, vector<double>& tau_errs)
{
  // chain: Markov chain to perform calculations on
  // means/vars/taus: vectors to which sample mean, sample variance, and autocorrelation time estimate are pushed back
  // mean_errs/var_errs/tau_errs: errors of above
  // sample variance according to http://www.metrology.pg.gda.pl/full/2010/M&MS_2010_003.pdf
  // variance of sample variance according to https://stats.stackexchange.com/questions/156518/what-is-the-standard-error-of-the-sample-standard-deviation

  int N = chain.size();
  if (N == 0) throw std::invalid_argument("chain must not be empty");

  double sample_mean = std::accumulate(chain.begin(), chain.end(), 0.) / N;

  double quadratic_sum = 0.;
  #pragma omp parallel for reduction(+:quadratic_sum)
  for (int n = 0; n < N; n ++) quadratic_sum += pow(chain[n] - sample_mean, 2);

  double tau_hat, tau_hat_err;
  autocorr(chain, tau_hat, tau_hat_err, sample_mean, quadratic_sum);
  double N_eff = N / tau_hat;

  double sample_mean_var = quadratic_sum / (N * (N_eff - 1.));
  double sample_var = N_eff * sample_mean_var;

  double sample_var_var;
  if (isnan(tau_hat)) sample_var_var = nan("");
  else
  {
    vector<double> thinned = thin(chain, ceil(tau_hat));
    int N_thin = thinned.size();
    double thinned_quartic_sum = 0.;
    #pragma omp parallel for reduction(+:thinned_quartic_sum)
    for (int n = 0; n < N_thin; n ++) thinned_quartic_sum += pow(thinned[n] - sample_mean, 4);
    sample_var_var = (thinned_quartic_sum/N_thin - (N_thin-3.)/(N_thin-1.)*sample_var*sample_var) / N_thin;
  }

  means.push_back(sample_mean);
  mean_errs.push_back(sqrt(sample_mean_var));
  vars.push_back(sample_var);
  var_errs.push_back(sqrt(sample_var_var));
  taus.push_back(tau_hat);
  tau_errs.push_back(tau_hat_err);
}
