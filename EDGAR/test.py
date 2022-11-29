from embedder import embedder


embedder = embedder(type='BERT')
cleaned_phrase = embedder.clean_phrase('hello, my name is     name ihjdfajaf ! ajflaj and I like sushi! food!food!', None)
print(cleaned_phrase)
if(embedder.type == 'BagOfWords'):
    embedder.add_dictionary(cleaned_phrase)
cleaned_phrase1 = embedder.clean_phrase('hello, hi netflix money', None)
print(cleaned_phrase1)
print(embedder.embed_phrase(cleaned_phrase))
print(embedder.embed_phrase(cleaned_phrase1))