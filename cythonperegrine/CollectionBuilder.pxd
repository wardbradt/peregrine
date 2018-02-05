from cpython cimport bool

cdef class CollectionBuilder:
    cdef list exchanges
    cdef dict collections
    cdef dict singularly_available_markets

cdef class SpecificCollectionBuilder(CollectionBuilder):
    cdef bool blacklist
    cdef dict rules

cpdef dict build_all_collections(CollectionBuilder builder, bool write)

cpdef dict build_specific_collections(dict rules, bool blacklist, bool write)
