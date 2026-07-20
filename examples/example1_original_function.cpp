std::vector<std::array<int, 5>> get_apple_variations(const int apples, const std::array<int, 5>& min_apples, int max_apples)
{
	const auto UPPER = max_apples;
	const auto SUM = apples;

	std::vector<std::array<int, 5>> apple_variations{};
	for (auto i = min_apples[0]; i <= std::min(UPPER, SUM); ++i)
	{
		auto SUM_i = SUM - i;
		for (auto j = min_apples[1]; j <= std::min(UPPER, SUM_i); ++j)
		{
			auto SUM_i_j = SUM_i - j;
			for (auto k = min_apples[2]; k <= std::min(UPPER, SUM_i_j); ++k)
			{
				auto SUM_i_j_k = SUM_i_j - k;
				for (auto l = min_apples[3]; l <= std::min(UPPER, SUM_i_j_k); ++l)
				{
					auto SUM_i_j_k_l = SUM_i_j_k - l;
					auto m = SUM_i_j_k_l;
					if (min_apples[4] <= m && m <= UPPER)
					{
						apple_variations.push_back({ i, j, k, l, m });
					}
				}
			}
		}
	}

	return apple_variations;
}
