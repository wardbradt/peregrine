cdef struct bid:
    char* exchange_name
    float price


cdef class OpportunityFinder:
    cdef list exchange_list
    cdef char* market_name
    cdef bid highest_bid
    cdef bid lowest_ask

    cpdef find_min_max(self)
