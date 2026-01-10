// Compute the four Hamiltonian components (HP, HC, HD, HB) for a provided electoral configuration. Accepts either an area directory name (which preserves the ED ordering used by the MCMC output) or a comma-separated county list that is looked up in data/ED_data.csv. Can thus use this on any arbitrary configuration, in particular useful for comparison with current constituency configuration.
//  Eg
//    compute_H "Cork_1000-200;2,1,0" "3,3,4,5,5" configs.csv
//    compute_H "CORK" "3,3,4,5,5" "0,0,1,1,..."

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <set>
#include <algorithm>
#include <cctype>
#include <valarray>
using std::valarray;
#include "../headers/Map.h"

static inline std::string trim(const std::string &s)
{
  size_t a = 0, b = s.size();
  while (a < b && std::isspace((unsigned char)s[a]))
    ++a;
  while (b > a && std::isspace((unsigned char)s[b - 1]))
    --b;
  return s.substr(a, b - a);
}

static std::vector<std::string> csv_split(const std::string &line) // Split a CSV line into fields, handling quoted fields that may contain commas
{
  std::vector<std::string> out;
  std::string cur;
  bool in_quotes = false;
  for (size_t i = 0; i < line.size(); ++i)
  {
    char c = line[i];
    if (c == '"')
    {
      in_quotes = !in_quotes;
    }
    else if (c == ',' && !in_quotes)
    {
      out.push_back(cur);
      cur.clear();
    }
    else
      cur.push_back(c);
  }
  out.push_back(cur);
  for (auto &s : out)
    s = trim(s);
  return out;
}

static std::vector<std::string> parse_neighbours_field(const std::string &fld) // Parse neighbour field of form { 'guid1', 'guid2' } or similar
{
  std::vector<std::string> nbs;
  // remove surrounding braces if present
  size_t a = 0, b = fld.size();
  while (a < b && (fld[a] == '{' || std::isspace((unsigned char)fld[a]) || fld[a] == '\'' || fld[a] == '"'))
    ++a;
  while (b > a && (fld[b - 1] == '}' || std::isspace((unsigned char)fld[b - 1]) || fld[b - 1] == '\'' || fld[b - 1] == '"'))
    --b;
  std::string core = (a < b) ? fld.substr(a, b - a) : std::string();
  std::string cur;
  bool in_quote = false;
  for (size_t i = 0; i < core.size(); ++i)
  {
    char c = core[i];
    if (c == '\'' || c == '"')
    {
      in_quote = !in_quote;
      continue;
    }
    if (c == ',' && !in_quote)
    {
      auto t = trim(cur);
      if (!t.empty())
        nbs.push_back(t);
      cur.clear();
    }
    else
      cur.push_back(c);
  }
  auto t = trim(cur);
  if (!t.empty())
    nbs.push_back(t);
  return nbs;
}

int main(int argc, char *argv[])
{
  if (argc < 4)
  {
    std::cerr << "Usage: compute_H <comma_separated_counties> <seats_comma_sep> <config_file_or_comma_list>\n";
    std::cerr << "Example: compute_H \"Cork,Dublin\" 3,3,4 0,0,1,1,...\n";
    return 1;
  }

  std::string counties_arg = argv[1];
  std::string seats_arg = argv[2];
  std::string cfg_arg = argv[3];


  std::set<std::string> county_set; // Parse counties set
  {
    std::stringstream ss(counties_arg);
    std::string tok;
    while (getline(ss, tok, ','))
    {
      tok = trim(tok);
      if (!tok.empty())
        county_set.insert(tok);
    }
  }
  if (county_set.empty())
  {
    std::cerr << "No counties provided\n";
    return 1;
  }

  std::vector<int> seats; // Parse seats config
  {
    std::stringstream ss(seats_arg);
    std::string tok;
    while (getline(ss, tok, ','))
    {
      tok = trim(tok);
      if (!tok.empty())
        seats.push_back(std::stoi(tok));
    }
  }
  if (seats.empty())
  {
    std::cerr << "No seats provided\n";
    return 1;
  }

  std::string area_dir = std::string("data/") + counties_arg + std::string("/"); // If the first argument names an existing area folder under data/, prefer that (keeps same ordering as configs.csv)
  std::vector<std::string> guids;
  std::vector<int> populations;
  std::vector<std::string> county_names;
  std::vector<std::vector<std::string>> raw_neighbours;
  std::vector<std::vector<int>> neighbours;

  std::ifstream edf;
  if (std::ifstream(area_dir + "Population.txt").good() && std::ifstream(area_dir + "Neighbours.txt").good() && std::ifstream(area_dir + "County.txt").good())
  {

    std::ifstream popf(area_dir + "Population.txt"); // Area-directory mode: read Population.txt, Neighbours.txt, County.txt to preserve ordering
    std::ifstream neif(area_dir + "Neighbours.txt");
    std::ifstream couf(area_dir + "County.txt");
    std::string line;
    while (std::getline(popf, line))
    {
      if (line.size())
        populations.push_back(std::stoi(trim(line)));
    }
    while (std::getline(neif, line))
    {

      std::stringstream nss(line); // Neighbours file in area mode is space-separated indices; parse ints
      int idx;
      std::vector<int> row;
      while (nss >> idx)
        row.push_back(idx);
      neighbours.push_back(row);
    }
    while (std::getline(couf, line))
    {
      county_names.push_back(trim(line));
    }
    popf.close();
    neif.close();
    couf.close();

    if (std::ifstream(area_dir + "GUID.txt").good()) // Construct guids vector from GUID.txt if available, otherwise create numeric guids
    {
      std::ifstream guidf(area_dir + "GUID.txt");
      while (std::getline(guidf, line))
      {
        guids.push_back(trim(line));
      }
      guidf.close();
    }
    else
    {

      for (size_t i = 0; i < populations.size(); ++i)
        guids.push_back(std::to_string(i)); // Fallback numeric guids
    }
    if (!(guids.size() == populations.size() && guids.size() == neighbours.size() && guids.size() == county_names.size()))
    {
      std::cerr << "Area files in " << area_dir << " have mismatched lengths (GUID/Population/Neighbours/County)\n";
      return 1;
    }
  }
  else
  {

    std::string data_fp = std::string("data/ED_data.csv"); // Open ED_data.csv
    edf.open(data_fp);
    if (!edf.is_open())
    {
      std::cerr << "Failed to open " << data_fp << "\n";
      return 1;
    }

    std::string header_line; // Read header to find column indices (we assume typical header order but use header names)
    if (!std::getline(edf, header_line))
    {
      std::cerr << "ED_data.csv is empty\n";
      return 1;
    }
    auto headers = csv_split(header_line);
    auto find_col = [&](const std::string &name) -> int
    {
      for (size_t i = 0; i < headers.size(); ++i)
        if (headers[i] == name)
          return (int)i;
      return -1;
    };
    int col_guid = find_col("GUID");
    int col_county = find_col("County");
    int col_population = find_col("Population");
    int col_neighbours = find_col("Neighbours");
    if (col_guid < 0 || col_county < 0 || col_population < 0 || col_neighbours < 0)
    {
      std::cerr << "ED_data.csv missing required columns (GUID, County, Population, Neighbours)\n";
      return 1;
    }

    std::string ln; // Collect selected EDs in file order
    while (std::getline(edf, ln))
    {
      if (ln.size() == 0)
        continue;
      auto fields = csv_split(ln);
      if ((int)fields.size() <= std::max({col_guid, col_county, col_population, col_neighbours}))
        continue;
      std::string guid = fields[col_guid];
      std::string county = fields[col_county];
      if (county_set.find(county) == county_set.end())
        continue; // Skip outside counties
      std::string pop_s = fields[col_population];
      std::string neigh_f = fields[col_neighbours];
      int pop = 0;
      try
      {
        pop = std::stoi(pop_s);
      }
      catch (...)
      {
        pop = 0;
      }

      guids.push_back(guid);
      populations.push_back(pop);
      county_names.push_back(county);
      raw_neighbours.push_back(parse_neighbours_field(neigh_f));
    }
    edf.close();

    if (guids.empty())
    {
      std::cerr << "No EDs found for provided counties\n";
      return 1;
    }

    std::unordered_map<std::string, int> guid_to_idx; // map GUID -> index
    for (size_t i = 0; i < guids.size(); ++i)
      guid_to_idx[guids[i]] = (int)i;
    // raw_neighbours holds per-ED lists of GUID strings (as extracted from ED_data.csv).
    // Each entry may itself contain comma-separated GUIDs; we'll split/map them below.

    // build neighbour indices, only keep neighbours within selected set
    if (neighbours.empty())
    {
      // Build numeric neighbour-index lists from GUID lists in raw_neighbours.
      neighbours.assign(guids.size(), std::vector<int>());
      for (size_t i = 0; i < raw_neighbours.size(); ++i)
      {
        for (auto &graw : raw_neighbours[i])
        {
          std::string token;
          std::stringstream ss(graw);
          while (std::getline(ss, token, ','))
          {
            token = trim(token);
            // Remove common surrounding characters if present
            while (!token.empty() && (token.back() == '\'' || token.back() == '"' || token.back() == '}' || token.back() == ','))
              token.pop_back();
            while (!token.empty() && (token.front() == '\'' || token.front() == '"' || token.front() == '{' || std::isspace((unsigned char)token.front())))
              token.erase(token.begin());
            if (token.empty())
              continue;
            auto it = guid_to_idx.find(token);
            if (it != guid_to_idx.end())
              neighbours[i].push_back(it->second);
          }
          // neighbours built
          size_t total_nb = 0;
          size_t max_nb = 0;
          for (auto &r : neighbours)
          {
            total_nb += r.size();
            max_nb = std::max(max_nb, r.size());
          }
        }
      }
    }

  }
  // compress county names into integers
  std::unordered_map<std::string, int> county_to_idx;
  std::vector<int> counties(guids.size());
  int next_c = 0;
  for (size_t i = 0; i < county_names.size(); ++i)
  {
    auto &cn = county_names[i];
    auto it = county_to_idx.find(cn);
    if (it == county_to_idx.end())
    {
      county_to_idx[cn] = next_c;
      counties[i] = next_c;
      ++next_c;
    }
    else
      counties[i] = it->second;
  }

  Map map(seats, populations, neighbours, counties); // Construct Map

  // parse configuration (file or comma-list)
  std::vector<int> config;
  std::ifstream cfgf(cfg_arg);
  if (cfgf.is_open())
  {
    std::string line;
    // try to find an 'optimals' block
    bool found = false;
    std::vector<std::string> lines;
    while (std::getline(cfgf, line))
      lines.push_back(line);
    cfgf.close();
    for (size_t i = 0; i < lines.size(); ++i)
    {
      if (lines[i] == "optimals")
      {
        size_t j = i + 1;
        while (j < lines.size() && lines[j].size() == 0)
          ++j;
        if (j < lines.size())
        {
          line = lines[j];
          found = true;
        }
        break;
      }
    }
    if (!found)
    {
      // take first non-empty line
      for (auto &l : lines)
        if (!l.empty())
        {
          line = l;
          found = true;
          break;
        }
    }
    if (!found)
    {
      std::cerr << "Config file was empty\n";
      return 1;
    }
    std::stringstream ss(line);
    std::string tok;
    while (getline(ss, tok, ','))
    {
      tok = trim(tok);
      if (!tok.empty())
        config.push_back(std::stoi(tok));
    }
  }
  else
  {
    // treat cfg_arg itself as comma list
    std::stringstream ss(cfg_arg);
    std::string tok;
    while (getline(ss, tok, ','))
    {
      tok = trim(tok);
      if (!tok.empty())
        config.push_back(std::stoi(tok));
    }
  }

  if (config.size() != map.EDs())
  {
    std::cerr << "Configuration length (" << config.size() << ") does not match number of EDs (" << map.EDs() << ")\n";
    return 1;
  }

  map.change_config(config);

  std::cerr << std::flush;
  valarray<double> H = map.H();
  std::cerr << std::flush;
  std::cout << "HP," << H[0] << "\n";
  std::cout << "HC," << H[1] << "\n";
  std::cout << "HD," << H[2] << "\n";
  std::cout << "HB," << H[3] << "\n";

  return 0;
}