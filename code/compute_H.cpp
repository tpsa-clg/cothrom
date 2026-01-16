// Streamlined implementation: assume area directory with ordered ED files
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>
#include <cctype>
#include <valarray>
using std::valarray;
#include "../headers/Map.h"

static inline std::string trim(const std::string &s)
{
  size_t a = 0, b = s.size();
  while (a < b && std::isspace((unsigned char)s[a])) ++a;
  while (b > a && std::isspace((unsigned char)s[b-1])) --b;
  return s.substr(a, b - a);
}

static std::vector<std::string> split_commas(const std::string &line)
{
  std::vector<std::string> out;
  std::stringstream ss(line);
  std::string tok;
  while (std::getline(ss, tok, ',')) { tok = trim(tok); if (!tok.empty()) out.push_back(tok); }
  return out;
}

int main(int argc, char *argv[])
{
  if (argc < 4)
  {
    std::cerr << "Usage: compute_H <area_folder> <seats_comma_sep> <configs.csv>\n";
    return 1;
  }

  std::string area_arg = argv[1];
  std::string seats_arg = argv[2];
  std::string configs_fp = argv[3];

  // parse seats
  std::vector<int> seats;
  for (auto &s : split_commas(seats_arg)) seats.push_back(std::stoi(s));
  if (seats.empty()) { std::cerr << "No seats provided\n"; return 1; }

  // area files (expects data/<area>/Population.txt etc.)
  std::string area_dir = std::string("data/") + area_arg + std::string("/");
  std::string pop_fp = area_dir + "Population.txt";
  std::string nei_fp = area_dir + "Neighbours.txt";
  std::string cou_fp = area_dir + "County.txt";
  std::string guid_fp = area_dir + "GUID.txt";

  // read populations
  std::ifstream popf(pop_fp);
  if (!popf.is_open()) { std::cerr << "Failed to open " << pop_fp << "\n"; return 1; }
  std::vector<int> populations; std::string line;
  while (std::getline(popf, line)) { line = trim(line); if (!line.empty()) populations.push_back(std::stoi(line)); }
  popf.close();

  // read neighbours (space-separated integer indices)
  std::ifstream neif(nei_fp);
  if (!neif.is_open()) { std::cerr << "Failed to open " << nei_fp << "\n"; return 1; }
  std::vector<std::vector<int>> neighbours;
  while (std::getline(neif, line))
  {
    line = trim(line);
    std::vector<int> row;
    if (!line.empty()) { std::stringstream ss(line); int idx; while (ss >> idx) row.push_back(idx); }
    neighbours.push_back(row);
  }
  neif.close();

  // county names
  std::ifstream couf(cou_fp);
  if (!couf.is_open()) { std::cerr << "Failed to open " << cou_fp << "\n"; return 1; }
  std::vector<std::string> county_names;
  while (std::getline(couf, line)) { county_names.push_back(trim(line)); }
  couf.close();

  // GUIDs optional (not required for computing H but kept for compatibility)
  std::vector<std::string> guids;
  std::ifstream guidf(guid_fp);
  if (guidf.is_open()) { while (std::getline(guidf, line)) guids.push_back(trim(line)); guidf.close(); }
  else { guids.resize(populations.size()); for (size_t i = 0; i < guids.size(); ++i) guids[i] = std::to_string(i); }

  if (!(populations.size() == neighbours.size() && populations.size() == county_names.size() && populations.size() == guids.size()))
  {
    std::cerr << "Area files have mismatched lengths (Population/Neighbours/County/GUID)\n";
    return 1;
  }

  // compress counties to integer ids
  std::unordered_map<std::string,int> county_to_idx;
  std::vector<int> counties(populations.size());
  int next_c = 0;
  for (size_t i = 0; i < county_names.size(); ++i)
  {
    auto &cn = county_names[i];
    auto it = county_to_idx.find(cn);
    if (it == county_to_idx.end()) { county_to_idx[cn] = next_c; counties[i] = next_c; ++next_c; }
    else counties[i] = it->second;
  }

  // read configs.csv and extract optimals or first numeric line
  std::ifstream cfgf(configs_fp);
  if (!cfgf.is_open()) { std::cerr << "Failed to open " << configs_fp << "\n"; return 1; }
  std::vector<std::string> lines;
  while (std::getline(cfgf, line)) lines.push_back(line);
  cfgf.close();

  std::string config_line;
  // prefer the 'optimals' block
  for (size_t i = 0; i + 1 < lines.size(); ++i)
  {
    if (trim(lines[i]) == "optimals")
    {
      size_t j = i + 1; while (j < lines.size() && trim(lines[j]).empty()) ++j;
      if (j < lines.size()) { config_line = trim(lines[j]); break; }
    }
  }
  if (config_line.empty())
  {
    // fallback to first numeric-looking non-empty line after optional 'initial' marker
    size_t start = 0;
    for (size_t i = 0; i < lines.size(); ++i) if (trim(lines[i]) == "initial") { start = i+1; break; }
    for (size_t i = start; i < lines.size(); ++i)
    {
      std::string t = trim(lines[i]); if (t.empty()) continue;
      bool has_digit = false; for (char c : t) if (std::isdigit((unsigned char)c)) { has_digit = true; break; }
      if (has_digit) { config_line = t; break; }
    }
  }
  if (config_line.empty()) { std::cerr << "No configuration line found in " << configs_fp << "\n"; return 1; }

  std::vector<int> config;
  for (auto &tok : split_commas(config_line)) config.push_back(std::stoi(tok));
  if (config.size() != populations.size()) { std::cerr << "Configuration length (" << config.size() << ") does not match number of EDs (" << populations.size() << ")\n"; return 1; }

  // Build Map and compute H
  Map map(seats, populations, neighbours, counties);
  map.change_config(config);
  valarray<double> H = map.H();
  std::cout << "HP," << H[0] << "\n";
  std::cout << "HC," << H[1] << "\n";
  std::cout << "HD," << H[2] << "\n";
  std::cout << "HB," << H[3] << "\n";

  return 0;
}
