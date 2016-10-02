#!/usr/bin/env python
# -*- coding:utf-8 -*-

from nltk.stem.snowball import SnowballStemmer
import cPickle as pickle
import os, re

directory = os.path.dirname(os.path.realpath(__file__))
ftoj = pickle.load(open(directory+'/train/ftoj.p', 'rb'))
stop_set = pickle.load(open(directory+'/train/stop_set.p', 'rb'))

def tokenize(text, avoid=None):    
    token_list = re.split('\s+', text)
    output = []
    web = ur"(?:https?://|www.)[\w\u00C0-\u00FF]+(?:[./?=-][\w\u00C0-\u00FF]+)*[/]?"
    special = ur"(?:[A-Z]?[\w$&][/.])+(?:[\w$&])*"
    date = ur"(?:[\d]+[/.])+[\d]+"
    song = ur"[Ff](?:[Ee][Aa])?[Tt]\.|[Vv][Ee][Rr]\.|[Pp]t\.|[Nn]o\.|[Oo]p\.|Mr\.|Ms\.|Jr\.|Dr\.|[Vv]s\."
    latin1 = ur"[$\w\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+"
    latin2 = ur"(?:[-'\u2018\u2019][$\w\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+)*|[.]{3}"
    latin_scripts = latin1 + latin2
    latin_punc = ur'[\u0021-\u002F]|[\u003A-\u0040]|[\u005B-\u0060]|[\u007B-\u007E]|[\u00A1-\u00BF]'
    cjk_scripts = ur'[\u4E00-\u9FFF]|[\u30A0-\u30FF]+|[\u3040-\u309F]+|[\uAC00-\uD7AF]+'
    cjk_punc = ur'[\u3000-\u303F]|[\uFF00-\uFFEF]'
    cyr_scripts = ur"[\d\u0400-\u04FF]+(?:[-.'\u2018\u2019][\d\u0400-\u04FF]+)*"
    cyr_special = ur"(?:[А-Я\d&]+\.)+"
    sa_scripts = ur'[\u0900-\u097F]+|[\uA8E0-\uA8FF]+|[\u1CD0-\u1CFF]+|[\u0980-\u09FF]+'
    arb_scripts = ur'[\u0600-\u06FF\u0750-\u077F]+'
    gre_scripts = ur'[\u0370-\u03FF\u1F00-\u1FFF]+'
    gen_punc = ur'[\u2000-\u206F]'
    mis_symbols = ur'[\u2600-\u26FF\u25A0-\u25FF]'
    if avoid is None:
        all_scripts = '|'.join([web, date, special, song, latin_scripts, 
                                latin_punc, cjk_scripts, cjk_punc,
                                cyr_scripts, cyr_special, sa_scripts, 
                                arb_scripts, gre_scripts, gen_punc, 
                                mis_symbols])
    elif avoid == 'nopunc':
        all_scripts = '|'.join([web, date, special, song, latin_scripts,
                                cjk_scripts, cyr_scripts, cyr_special, 
                                sa_scripts, arb_scripts, gre_scripts,
                                mis_symbols])
    pattern = re.compile(all_scripts)
    for token in token_list:
        subtoken_list = re.findall(pattern, token)
        for subtoken in subtoken_list:
            output.append(subtoken)
    return output


#stem a token (not a whole sentence) from a tokenizer
def stem(token):
    latin = ur"[\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]"
    jk_scripts = ur'[\u30A0-\u30FF]|[\u3040-\u309F]|[\uAC00-\uD7AF]'
    ch_scripts = ur'[\u4E00-\u9FFF]'
    cjk_punc = ur'[\u3000-\u303F]|[\uFF00-\uFFEF]'
    cyr_scripts = ur'[\u0400-\u04FF]'
    sa_scripts = ur'[\u0900-\u097F]|[\uA8E0-\uA8FF]|[\u1CD0-\u1CFF]|[\u0980-\u09FF]'
    arb_scripts = ur'[\u0600-\u06FF\u0750-\u077F]'
    gre_scripts = ur'[\u0370-\u03FF\u1F00-\u1FFF]'
    gen_punc = ur'[\u2000-\u206F]'
    mis_symbols = ur'[\u2600-\u26FF]'
    feat = ur'featur(?:e|ing)|f(?:ea)?t[.]?'
    ver = ur'ver(?:\.|sion)'
    vs = ur'v(?:ersu)?[.]?s[.]?'
    non_eng = '|'.join([latin, jk_scripts, cjk_punc, sa_scripts, arb_scripts, 
                        gre_scripts, gen_punc, mis_symbols])
    non_eng_pattern = re.compile(non_eng)
    ru_pattern = re.compile(cyr_scripts)
    ch_pattern = re.compile(ch_scripts)
    quotation = re.compile(ur"[\u2018\u2019]")
    comma = re.compile(ur"，")
    aand = re.compile(ur"[&+]+")
    feat_pattern = re.compile(feat, re.IGNORECASE)
    ver_pattern = re.compile(ver, re.IGNORECASE)
    vs_pattern = re.compile(vs, re.IGNORECASE)
    hyphen_pattern = re.compile(ur"[\uff0d\u2013\u2192]", 
                                re.IGNORECASE)
    token = re.sub(quotation, u"'", token)
    token= re.sub(comma, u",", token)
    #token = re.sub(aand, u"&", token)
    token = re.sub(feat_pattern, u"ft", token)
    token = re.sub(ver_pattern, u"ver", token)
    token = re.sub(vs_pattern, u"vs", token)
    token = re.sub(hyphen_pattern, u'-', token)
    if re.search(ch_pattern, token):
        return ch_stem(token)
    if re.search(non_eng_pattern, token):
        return token.lower()
    if re.search(ru_pattern, token):
        return SnowballStemmer('russian').stem(token)
    return SnowballStemmer('english').stem(token)


#transform any Chinese string into Simplified Chinese
def ch_stem(text):
    result = ''
    for char in text:
        stem_char = ftoj.get(char, char)
        result += stem_char
    return result

#further tokenize term with hypen in the middle 
def hypen_tokenize(text):
    latin = ur"[\w\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u0400-\u04FF]+|[-]"
    pattern = re.compile(latin)
    token_list = re.findall(pattern, text)
    return token_list


#geting file length
def get_file_length(filepath):
    count = 0
    with open(filepath, 'rb') as f:
        for line in f:
            count += 1
    return count           


