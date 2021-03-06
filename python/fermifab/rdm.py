import numpy as np
from scipy.sparse import csr_matrix
from .fermistate import FermiState
from .fermiop import FermiOp
from .util import trace_prod
from fermifab.kernel import gen_rdm

__all__ = ['rdm']


def construct_rdm_kernel(orbs, p1, N1, N2):
    """
    Generate the kernel K (as array of sparse matrices) required for
    calculating p-body reduced density matrices.
    """
    # convert to iterable tuples, if necessary
    if not hasattr(orbs, '__len__'): orbs = (orbs,)
    if not hasattr(p1,   '__len__'): p1   = (p1,)
    if not hasattr(N1,   '__len__'): N1   = (N1,)
    if not hasattr(N2,   '__len__'): N2   = (N2,)
    dims, val, ind = gen_rdm(orbs, p1, N1, N2)
    # store data in nested lists
    val_arr = [[[] for j in range(dims[1])] for i in range(dims[0])]
    row_arr = [[[] for j in range(dims[1])] for i in range(dims[0])]
    col_arr = [[[] for j in range(dims[1])] for i in range(dims[0])]
    for n in range(len(ind)):
        val_arr[ind[n, 0]][ind[n, 1]].append(val[n])
        row_arr[ind[n, 0]][ind[n, 1]].append(ind[n, 2])
        col_arr[ind[n, 0]][ind[n, 1]].append(ind[n, 3])
    K = [[csr_matrix((val_arr[i][j], (row_arr[i][j], col_arr[i][j])), shape=(dims[2], dims[3]))
            for j in range(dims[1])]
            for i in range(dims[0])]
    return K


def rdm(state, p):
    """
    Calculate the p-body reduced density matrix of a N-body quantum state.

    Args:
        state: quantum state of type 'FermiState'
        p:     target particle number

    Returns:
        numpy.ndarray: reduced density matrix
    """
    if type(state) == FermiState:
        N1 = state.N
        N2 = N1
    elif type(state) == FermiOp:
        N1 = state.pFrom
        N2 = state.pTo
        # TODO: add support for lists of N
        assert N1 == N2

    K = construct_rdm_kernel(state.orbs, p, N1, N2)
    G = np.zeros((len(K), len(K[0])), dtype=state.data.dtype)
    for i in range(G.shape[0]):
        for j in range(G.shape[1]):
            if type(state) == FermiState:
                G[i, j] = np.vdot(state.data, K[i][j].dot(state.data))
            else:
                G[i, j] = trace_prod(K[i][j], state.data)

    return FermiOp(state.orbs, p, p, data=G)
