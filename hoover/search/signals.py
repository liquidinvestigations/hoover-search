from django.dispatch import Signal

search = Signal(['request', 'collections', 'duration', 'success'])
doc = Signal(['request', 'collection', 'doc_id', 'duration', 'success'])
