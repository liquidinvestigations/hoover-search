from django.dispatch import Signal

search = Signal(['request', 'collections', 'duration', 'success'])
doc = Signal(['request', 'collection', 'doc_id', 'duration', 'success'])
batch = Signal(['request', 'collections', 'duration', 'success', 'query_count'])
rate_limit_exceeded = Signal(['username'])
