    """
This code is aimed to provide tools for prediction process. 
    """



def predictions(params, history, alpha, mu, T = None):
    """
    Returns the expected total numbers of points for a set of time points
    
    params   -- parameter tuple (p,beta) of the Hawkes process
    history  -- (n,2) numpy array containing marked time points (t_i,m_i)  
    alpha    -- power parameter of the power-law mark distribution
    mu       -- min value parameter of the power-law mark distribution
    T        -- 1D-array of times (i.e ends of observation window)
    """

    p,beta = params
    
    tis = history[:,0]
    if T is None:
        T = np.linspace(60,tis[-1],1000)

    N = np.zeros((len(T),2))
    N[:,0] = T
    
    EM = mu * (alpha - 1) / (alpha - 2)
    n_star = p * EM
    if n_star >= 1:
        raise Exception(f"Branching factor {n_star:.2f} greater than one")

    Si, ti_prev, i = 0., 0., 0
    
    for j,t in enumerate(T):
        for (ti,mi) in history[i:]:
            if ti >= t:
                break
            else:
                Si = Si * np.exp(-beta * (ti - ti_prev)) + mi
                ti_prev = ti
                i += 1

        n = i + 1
        G1 = p * Si * np.exp(-beta * (t - ti_prev))
        N[j,1] = n + G1 / (1. - n_star)
    return N