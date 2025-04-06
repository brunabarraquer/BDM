import random
import nltk
from nltk.corpus import wordnet


nltk.download('wordnet')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# Base templates for different sentiment categories
positive_templates = [
    "The movie was {adj_pos}! {noun_pos} was {adj_pos} and the {noun_pos} was {adj_pos}.",
    "{adv_pos} {adj_pos} film! The {noun_pos} {verb_pos} me from start to finish.",
    "I {adv_pos} {verb_pos} this movie. The {noun_pos} was {adj_pos}.",
    "A {adj_pos} {noun_pos} with {adj_pos} {noun_pos} and {adj_pos} {noun_pos}.",
    "The {noun_pos} was {adj_pos} and the {noun_pos} was {adv_pos} {adj_pos}.",
    "What a {adj_pos} experience! {noun_pos} was {adj_pos} and {noun_pos} was {adj_pos}.",
    "{adj_pos} from beginning to end! The {noun_pos} {adv_pos} {verb_pos}.",
    "The {noun_pos} was {adj_pos}, making it a {adj_pos} {noun_pos} to watch."
]

mixed_templates = [
    "The {noun_pos} was {adj_pos}, but the {noun_neg} was {adj_neg}.",
    "{adj_pos} {noun_pos}, however the {noun_neg} was {adv_neg} {adj_neg}.",
    "Despite the {adj_pos} {noun_pos}, the {noun_neg} {verb_neg} {adv_neg}.",
    "A {adj_mixed} film with {adj_pos} {noun_pos} but {adj_neg} {noun_neg}.",
    "The {noun_pos} {verb_pos}, although the {noun_neg} {verb_neg} at times.",
    "{adj_mixed} overall. {noun_pos} was {adj_pos} while {noun_neg} was {adj_neg}.",
    "Not {adv_neg} {adj_neg}, but not {adv_pos} {adj_pos} either. Just {adj_mixed}."
]

negative_templates = [
    "The movie was {adj_neg}. The {noun_neg} was {adj_neg} and the {noun_neg} was {adj_neg}.",
    "{adv_neg} {adj_neg}! The {noun_neg} {verb_neg} throughout the entire film.",
    "I {verb_neg} this movie. The {noun_neg} was {adj_neg}.",
    "A {adj_neg} {noun_neg} with {adj_neg} {noun_neg} and {adj_neg} {noun_neg}.",
    "The {noun_neg} was {adj_neg} and the {noun_neg} was {adv_neg} {adj_neg}.",
    "What a {adj_neg} experience! {noun_neg} was {adj_neg} and {noun_neg} was {adj_neg}.",
    "{adj_neg} from beginning to end! The {noun_neg} {adv_neg} {verb_neg}.",
    "The {noun_neg} was {adj_neg}, making it a {adj_neg} {noun_neg} to watch."
]

# Word banks for different parts of speech and sentiments
words = {
    'adj_pos': ['amazing', 'fantastic', 'excellent', 'outstanding', 'brilliant', 'superb', 
                'incredible', 'wonderful', 'exceptional', 'phenomenal', 'marvelous', 'stunning', 
                'impressive', 'captivating', 'engaging', 'enthralling', 'breathtaking', 'powerful',
                'remarkable', 'extraordinary', 'innovative', 'masterful', 'riveting', 'moving',
                'delightful', 'enchanting', 'memorable', 'profound', 'fascinating', 'compelling'],
    
    'adj_neg': ['terrible', 'awful', 'disappointing', 'poor', 'dreadful', 'horrible', 'mediocre',
               'weak', 'bland', 'boring', 'tedious', 'dull', 'uninspired', 'forgettable', 'predictable',
               'shallow', 'confusing', 'frustrating', 'annoying', 'ridiculous', 'silly', 'nonsensical',
               'contrived', 'pretentious', 'unoriginal', 'clichéd', 'trite', 'insipid', 'lackluster',
               'overrated'],
    
    'adj_mixed': ['decent', 'adequate', 'fair', 'moderate', 'passable', 'reasonable', 'average', 
                 'okay', 'so-so', 'mixed', 'inconsistent', 'uneven', 'middle-of-the-road', 'ordinary',
                 'conventional', 'standard', 'run-of-the-mill', 'serviceable', 'tolerable', 'acceptable'],
    
    'noun_pos': ['story', 'plot', 'acting', 'direction', 'cinematography', 'script', 'dialogue', 
                'performance', 'visuals', 'characters', 'editing', 'pacing', 'soundtrack', 'cast',
                'production', 'special effects', 'narrative', 'screenplay', 'development', 'execution',
                'atmosphere', 'theme', 'music', 'imagery', 'photography', 'tone', 'setting'],
    
    'noun_neg': ['screenplay', 'storyline', 'dialogue', 'pacing', 'editing', 'character development',
                'plot holes', 'resolution', 'ending', 'acting', 'direction', 'script', 'special effects',
                'CGI', 'writing', 'performances', 'execution', 'narrative', 'climax', 'twist',
                'characterization', 'premise', 'concept', 'soundtrack', 'scenes', 'sequence', 'flow'],
    
    'verb_pos': ['enjoyed', 'loved', 'appreciated', 'adored', 'treasured', 'savored', 'admired',
                'praised', 'celebrated', 'cherished', 'embraced', 'valued', 'respected', 'captivated',
                'impressed', 'moved', 'touched', 'inspired', 'engaged', 'enthralled', 'fascinated'],
    
    'verb_neg': ['disliked', 'hated', 'detested', 'criticized', 'condemned', 'disapproved of', 'loathed',
                'despised', 'dismissed', 'rejected', 'panned', 'denounced', 'slammed', 'resented',
                'regretted', 'minded', 'objected to', 'opposed', 'bemoaned', 'lamented', 'deplored'],
    
    'adv_pos': ['extremely', 'incredibly', 'remarkably', 'truly', 'genuinely', 'thoroughly', 'absolutely',
               'completely', 'totally', 'wholly', 'deeply', 'immensely', 'greatly', 'highly', 'intensely',
               'profoundly', 'exceptionally', 'extraordinarily', 'tremendously', 'vastly', 'enormously'],
    
    'adv_neg': ['extremely', 'incredibly', 'remarkably', 'truly', 'genuinely', 'thoroughly', 'absolutely',
               'completely', 'totally', 'wholly', 'deeply', 'immensely', 'greatly', 'highly', 'intensely',
               'profoundly', 'woefully', 'terribly', 'horribly', 'painfully', 'unbearably', 'dismally']
}


# Function to get synonyms
def get_synonyms(word, pos=None):
    synonyms = set()
    for synset in wordnet.synsets(word, pos=pos):
        for lemma in synset.lemmas():
            synonym = lemma.name().replace('_', ' ')
            if synonym != word and len(synonym) > 3:  # Avoid very short words
                synonyms.add(synonym)
    return list(synonyms)


# Enrich the word banks with synonyms
# expand_factor ensures how many synonyms we want to add for each word
def enrich_wordbank(word_dict, expand_factor=3):
    expanded_dict = {}
    for category, word_list in word_dict.items():
        expanded = set(word_list)
        
        # Set POS tag based on category prefix
        pos = None
        if category.startswith('adj'):
            pos = wordnet.ADJ
        elif category.startswith('noun'):
            pos = wordnet.NOUN
        elif category.startswith('verb'):
            pos = wordnet.VERB
        elif category.startswith('adv'):
            pos = wordnet.ADV
            
        # Get synonyms for each word
        for word in word_list:
            synonyms = get_synonyms(word, pos)
            # We get the minimum of the sample size, it just can be <= 3
            sample_size = min(expand_factor, len(synonyms))
            if sample_size > 0:
                # Here we select the synonyms that we wanna add in our list randomly
                expanded.update(random.sample(synonyms, sample_size))
        
        expanded_dict[category] = list(expanded)
    return expanded_dict


# Expand the word banks
enriched_words = enrich_wordbank(words)


# Function to generate reviews using templates
def generate_review(templates, word_dict, capitalize_first=True):
    template = random.choice(templates)
    
    # Replace placeholders with random words from appropriate categories
    for category, words_list in word_dict.items():
        while '{' + category + '}' in template:
            replacement = random.choice(words_list)
            template = template.replace('{' + category + '}', replacement, 1)
    

    # Clean up the text
    sentences = template.split('. ')
    cleaned_sentences = []
    
    for sentence in sentences:
        # Capitalize first letter
        if capitalize_first and sentence:
            sentence = sentence[0].upper() + sentence[1:]
        # Add to cleaned sentences
        cleaned_sentences.append(sentence)
    
    # Join sentences back together
    review = '. '.join(cleaned_sentences)
    
    # Fix any double spaces
    review = ' '.join(review.split())
    
    # Ensure there's a period at the end if needed
    if review and not review.endswith(('.', '!', '?')):
        review += '.'
        
    return review


# Generate a large bank of reviews
def generate_review_bank(num_reviews=1000):
    reviews = []
    for _ in range(num_reviews):
        sentiment = random.choices(['positive', 'mixed', 'negative'], weights=[0.5, 0.25, 0.25])[0]
        
        if sentiment == 'positive':
            review = generate_review(positive_templates, enriched_words)
        elif sentiment == 'mixed':
            review = generate_review(mixed_templates, enriched_words)
        else:
            review = generate_review(negative_templates, enriched_words)
            
        reviews.append(review)
    
    return reviews
