def naive(SUM, min0, min1, min2, min3, min4, UPPER):
    result = 0
    for i in range(min0, min(UPPER, SUM) + 1):
        SUM_i = SUM - i
        for j in range(min1, min(UPPER, SUM_i) + 1):
            SUM_i_j = SUM_i - j
            for k in range(min2, min(UPPER, SUM_i_j) + 1):
                SUM_i_j_k = SUM_i_j - k
                for l in range(min3, min(UPPER, SUM_i_j_k) + 1):
                    SUM_i_j_k_l = SUM_i_j_k - l
                    m = SUM_i_j_k_l
                    if (min4 <= m) & (m <= UPPER):
                        result += 1
    return result