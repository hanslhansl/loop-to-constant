using Stats = std::array<int, 5>;
constexpr std::vector<Stats> get_stat_variations(const int attribute_points, const Stats& min_stats)
{
	constexpr auto UPPER = 99;
	const auto SUM = attribute_points;

	std::vector<Stats> stat_variations{};
	for (auto i = min_stats[0]; i <= std::min(UPPER, SUM); ++i)
	{
		auto SUM_i = SUM - i;
		for (auto j = min_stats[1]; j <= std::min(UPPER, SUM_i); ++j)
		{
			auto SUM_i_j = SUM_i - j;
			for (auto k = min_stats[2]; k <= std::min(UPPER, SUM_i_j); ++k)
			{
				auto SUM_i_j_k = SUM_i_j - k;
				for (auto l = min_stats[3]; l <= std::min(UPPER, SUM_i_j_k); ++l)
				{
					auto SUM_i_j_k_l = SUM_i_j_k - l;
					auto m = SUM_i_j_k_l;
					if (min_stats[4] <= m && m <= UPPER)
					{
						Stats indices = { i, j, k, l, m };
						stat_variations.push_back({ i, j, k, l, m });
					}
				}
			}
		}
	}

	return stat_variations;
}
