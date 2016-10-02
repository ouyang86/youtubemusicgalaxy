#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from youtube import *
from math import log, exp
import json, urllib, os
import gc, sqlite3
import cPickle as pickle

punc_pair = {u'[':u']', u'"': u'"', u'(':u')', u'{': u'}', u'（': u'）',
             u'《': u'》', u'【': u'】', u'〖': u'〗', u'「':u'」',
             u'『':u'』', u'“':u'”', u'«':u'»', u"'":u"'", u"☼":u"☼",
             u'〜':u'〜', u'◄':u'►', u'':u''}

#directory = '/var/www/MusicGalaxy/MusicGalaxy'
directory = os.path.dirname(os.path.realpath(__file__))
states = ['SONG', 'ARTIST', 'OTHER', 'FEAT', 'SEP', 'JOIN']
emit_p = pickle.load(open(directory+'/train/emit_p.p', 'rb'))
trans_p = pickle.load(open(directory+'/train/tran_p.p', 'rb'))
start_p = pickle.load(open(directory+'/train/start_p.p', 'rb'))
coef = pickle.load(open(directory+'/train/coef.p', 'rb'))
token_dict = pickle.load(open(directory+'/train/token_dict.p', 'rb'))


#training for artist name using MusicBrianz data
def train_artist(filepath, fields, weights,seperator,splitor,
                 normalize=False, logalize=False):
    result = {}
    avoid_token_list = set([u"part", u"pt.", u"no.", u"op.", u"vs.",u"vs",
                        u"feat", u"feat.", u"ft.", u"ft",  u"-", u"'",
                        u"bwv", u"k."])
    special = ur"(?:[A-Z]?[\w$&][/.])+(?:[\w$&])*"
    date = ur"(?:[\d]+[/.])+[\d]+"
    song = ur"[Ff](?:[Ee][Aa])?[Tt]\.|[Vv][Ee][Rr]\.|[Pp]t\.|[Nn]o\.|[Oo]p\.|Mr\.|Ms\.|Jr\.|Dr\.|[Vv]s\."
    latin1 = ur"[$\w\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+"
    latin2 = ur"(?:[-'\u2018\u2019][$\w\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+)*|[.]{3}"
    latin_scripts = latin1 + latin2
    latin_punc = ur"[!$%\-&']"
    cjk_scripts = ur'[\u4E00-\u9FFF]|[\u30A0-\u30FF]+|[\u3040-\u309F]+|[\uAC00-\uD7AF]+'
    cyr_scripts = ur"[\d\u0400-\u04FF]+(?:[-.'\u2018\u2019][\d\u0400-\u04FF]+)*"
    cyr_special = ur"(?:[А-Я\d&]+\.)+"
    sa_scripts = ur'[\u0900-\u097F]+|[\uA8E0-\uA8FF]+|[\u1CD0-\u1CFF]+|[\u0980-\u09FF]+'
    arb_scripts = ur'[\u0600-\u06FF\u0750-\u077F]+'
    gre_scripts = ur'[\u0370-\u03FF\u1F00-\u1FFF]+'
    all_scripts = '|'.join([special, date, song, latin_scripts, latin_punc, cjk_scripts, cyr_scripts, 
                            cyr_special, sa_scripts,  arb_scripts, gre_scripts])
    pattern = re.compile(all_scripts)
    with open(filepath, 'rb') as f:
        for line in f:
            record = line.decode('utf-8').strip('\n')
            entries = record.split(seperator)
            for field, weight in zip(fields, weights):
                record = entries[field]
                token_list = re.split(splitor,record)
                for token in token_list:
                    subtoken_list = re.findall(pattern, token)
                    for subtoken in subtoken_list:
                        if subtoken.lower() in avoid_token_list:
                            break
                        subtoken = stem(subtoken)
                        result[subtoken] = result.get(subtoken, 0) + weight
    if normalize:
        normalize_dict(result)
        if logalize:
            prob_to_log(result)
    return result


#training for song/music name using MusicBrainz data
def train_song(filepath, seperator ,field, normalize=False,
               logalize=False):
    result = {}
    stem_result = {}
    avoid = ur'[][":;~(){}/：；～（）《》【】〖〗「」『』“”«»☼〜◄►]|[\d]+(?:[-/.][\d]+)+'
    avoid_pat = re.compile(avoid)
    avoid_token_list = set([u"part", u"pt.", u"no.", u"op.", u"vs.",u"vs",
                        u"feat", u"feat.", u"ft.", u"ft",  u"-", u"'",
                        u"bwv", u"k."])
    with open(filepath, 'rb') as f:
        for line in f:
            record = line.decode('utf-8').strip('\n')
            entries = record.split(seperator)
            entry = entries[field]
            if re.search(avoid_pat, entry):
                continue
            token_list = tokenize(entry)
            avoid_entry = False
            for token in token_list:
                if token.lower() in avoid_token_list:
                    avoid_entry = True
                    break
            if avoid_entry:
                continue
            for token in token_list:
                if token:
                    token = token.lower()
                    result[token] = result.get(token, 0.0) + 1
    for token in result:
        freq = result[token]
        token = stem(token)
        stem_result[token] = stem_result.get(token, 0.0) + freq
    del result
    if normalize:
        normalize_dict(stem_result)
        if logalize:
            prob_to_log(stem_result)
    return stem_result


#train for music description text using MusicBrainz data
def train_other(insources, seperator,  normalize=False,
                logalize=False):
    result = {}
    avoid = ur'[][":;~(){}/：；～（）《》【】〖〗「」『』“”«»☼〜◄►]|ft'
    avoid_pat = re.compile(avoid)
    for source in insources:
        infile, field = source
        with open(infile, 'rb') as f:
            for line in f:
                line = line.decode('utf-8').strip('\n')
                entries = line.split(seperator)
                entry = entries[field]
                for token in tokenize(entry):
                    if re.search(avoid_pat, token):
                        continue
                    token = stem(token)
                    result[token] = result.get(token, 0) + 1.0
    if normalize:
        normalize_dict(result)
        if logalize:
            prob_to_log(result)
    return result
 

#adjusting song name or artist name training dictionary
def adjust(avoid, candidate, threshold = 10):
    avoid_total = sum(avoid.values())
    cand_total = sum(candidate.values())
    cjk_scripts = ur'[\u4E00-\u9FFF]|[\u30A0-\u30FF]|[\u3040-\u309F]|[\uAC00-\uD7AF]'
    cjk_pat = re.compile(cjk_scripts)
    for key in avoid:
        if re.search(cjk_pat, key):
            continue
        avoid_pct = avoid[key] / avoid_total
        cand_pct = candidate.get(key, 0.0) / cand_total
        if avoid_pct > cand_pct * threshold:
            candidate.pop(key, None)
            
            
#write a dictionary into a file
def write_dict(input_dict, filepath, reverse=True, seperator='<SEP>'):
    input_list = [(input_dict.get(key, ''), key) for key in input_dict]
    input_list.sort(reverse=reverse)
    with open(filepath, 'wb') as f:
        for item in input_list:
            record = '<SEP>'.join([item[1], unicode(item[0])])+u'\n'
            f.write(record.encode('utf-8'))
            

#normalize a dictionary into a probability distribution            
def normalize_dict(input_dict):
    total = sum(input_dict.values())*1.0
    for key in input_dict:
        input_dict[key] /= total


#change probability into log scale        
def prob_to_log(input_dict):
    for key in input_dict:
        value = input_dict[key]
        input_dict[key] = log(value)
        
        
#use this function for tokenization list before applying
#the Viterbi algorithm
#giving tag to paranthesis and quation
def punc_tag(entry):
    seperator = u'-:~'  
    start_quat = u'"「『《“«'+u"'"
    end_quat = u'"」』》”»'+u"'"
    start_para = u'[({（【〖☼〜◄'
    end_para = u'])}）】〗☼〜►'
    wait = []
    stack = []
    result = []
    for i, token in enumerate(entry):
        token = stem(token)
        tag = 'OTHER'
        """
        if token in seperator:
            tag = u'SEP'
        """
        if token not in wait and token in start_quat:
            stack.append((i, token))
            wait.append(punc_pair[token])
        elif token in wait and token in end_quat:
            check = wait.pop()
            ind, start_token = stack.pop()
            while token != check:
                check = wait.pop()
                ind, start_token = stack.pop()
            result[ind] = (start_token, u'SQ')
            tag = u'EQ'
        elif token not in wait and token in start_para:
            stack.append((i, token))
            wait.append(punc_pair[token])
        elif token in wait and token in end_para:
            check = wait.pop()
            ind, start_token = stack.pop()
            while token != check:
                check = wait.pop()
                ind, start_token = stack.pop()
            result[ind] = (start_token, u'SP')
            tag = u'EP'
        result.append((token, tag))
    return result
    

#tag_ind is the index of the youtube video title column in the input
#data set    
def trans_sep(infile, tag_ind, normalize=True, logalize=False):
    write_out = False
    required = set(['SONG', 'ARTIST', 'OTHER', 'FEAT',
                    'SONG-', 'ARTIST-', 'OTHER-', 
                    'SONG&', 'ARTIST&', 'OTHER&',
                    'SEP','JOIN'])
    tran_dict = {}
    count = 1
    with open(infile, 'rb') as f:
        for line in f:
            record = line.decode('utf-8').strip('\n')
            entries = record.split('<SEP>')
            tokentag_list = entries[tag_ind].split('<and>')
            if len(tokentag_list) < 2:
                count += 1
                continue
            pre_tag = tokentag_list[0].split('<tag>')[1]
            for tokentag in tokentag_list[1:]:
                cur_tag = tokentag.split('<tag>')[1]
                if pre_tag in required or cur_tag in required:
                    if pre_tag not in set(['EP', 'EP-', 'EP&']): 
                       #cur_tag not in set(['SP', 'SP-', 'SP&']):
                        if pre_tag in set(['FEAT', 'FEAT-', 'FEAT&']):
                            cur_tag = 'ARTIST'
                        if cur_tag in set(['SP', 'SP-', 'SP&']):
                            cur_tag = u'END'
                        temp = tran_dict.get(pre_tag, {})
                        temp[cur_tag] = temp.get(cur_tag, 0) + 1.0
                        tran_dict[pre_tag] = temp
                        
                """
                if pre_tag == 'ARTIST&' and cur_tag == 'OTHER':
                    print count
                """
                if cur_tag == 'SEP':
                    cur_tag = pre_tag.rstrip('[-&]')+'-'
                    if cur_tag in set(['SP-', 'SQ-', 'FEAT-']):
                        cur_tag.rstrip('-')
                elif cur_tag == 'JOIN':
                    cur_tag = pre_tag.rstrip('[-&]')+'&'
                    if cur_tag in set(['SP&', 'SQ&', 'FEAT&']):
                        cur_tag.rstrip('&')
                pre_tag = cur_tag
            #if write_out == True:
            #    f1.write(line)
            if pre_tag in required:
                temp = tran_dict.get(pre_tag, {})
                temp[u'END'] = temp.get(u'END', 0) + 1.0
            count += 1
            write_out = False
    tt = tran_dict['FEAT'].pop(u'END', None)
    if normalize is True:
        for tag in tran_dict:
            value = tran_dict[tag]
            normalize_dict(value)
            if logalize is True:
                prob_to_log(value)
            tran_dict[tag] = value
    for key in set(['SP-', 'SQ-', 'FEAT-',
                    'SP&', 'SQ&', 'FEAT&']):
        tran_dict[key] = tran_dict[key.rstrip('[-&]')]
    if normalize and logalize:
        tran_dict['SONG&']['JOIN'] = tran_dict['SONG&'].get('JOIN', -2)
        tran_dict['ARTIST&']['JOIN'] = tran_dict['ARTIST&'].get('JOIN', -2)
        tran_dict['OTHER&']['JOIN'] = tran_dict['OTHER&'].get('JOIN', -2)
        tran_dict['EQ&'] = tran_dict.setdefault('EQ&', 
                           {'EQ': log(0.5), 'SONG': log(0.5)})
    return tran_dict



    
#tag_ind is the index of youtube video title column in the 
def start(infile, tag_ind, normalize=True, logalize=False):
    start_dict = {}
    required = set(['SONG', 'ARTIST', 'OTHER', 'FEAT', 'SEP', 'JOIN'])
    with open(infile, 'rb') as f:
        for line in f:
            record = line.decode('utf-8').strip('\n')
            entries = record.split('<SEP>')
            tokentag_list = entries[tag_ind].split('<and>')
            for tokentag in tokentag_list:
                twins= tokentag.split('<tag>')
                if len(twins) != 2:
                    continue
                tag = twins[1]
                if tag in required:
                    start_dict[tag] = start_dict.get(tag, 0) + 1.0
    if normalize is True:
        normalize_dict(start_dict)
        if logalize is True:
            prob_to_log(start_dict)
    return start_dict


#stag is the tag we explore for token distribution
#possible values for stag is 'SONG', 'ARTIST', 'OTHER', 'FEAT' 
#and 'SEP', 'JOIN'
#tag_ind is the index of youtube video title colun in the input
#dataset
def token_dist(infile, stag, tag_ind, basic=None, normalize=True,
               logalize=False):
    count = 1
    if basic is None:
        token_dict = {}
    else:
        token_dict = basic
    temp = token_dict.pop(u'ft', None)
    with open(infile, 'rb') as f:
        for line in f:
            record = line.decode('utf-8').strip('\n')
            entries = record.split('<SEP>')
            tokentag_list = entries[tag_ind].split('<and>')
            for tokentag in tokentag_list:
                twins = tokentag.split('<tag>')
                if len(twins) != 2:
                    continue
                token = twins[0]
                tag = twins[1]
                if token == u'ft':
                    tag = 'FEAT'
                if tag == stag:
                   token_dict[token] = token_dict.get(token, 0) + 1.0
    if normalize is True:
        normalize_dict(token_dict)
        if logalize is True:
            prob_to_log(token_dict)
    return token_dict   
    
    
#functions implements Viterbi Algorithm
def viterbi(obs, details = False, stemmer=False):
    """
    obs is a list of text tokens without punctuation tag [];
    states is a k-list of all k possible states of Markov Process;
    start_p is a k-dict of probabilities of all k possible states;
    trans_p is a k*k-dict of all transition probabilities among
    k possible states;
    emit_p is a k-dict of m-dict of probabilities of observing all 
    m possible tokens in a given state
    
    """
    punc = set(['SP','SQ', 'EP', 'EQ', 
                'SP-','SQ-', 'EP-', 'EQ-',
                'SP&', 'SQ&', 'EP&', 'EQ&'])
    end_punc = set(['SP', 'SP-', 'SP&'])
    web = ur"(?:https?://|www.)[\w\u00C0-\u00FF]+(?:[./?=-][\w\u00C0-\u00FF]+)*[/]?"
    web_pat = re.compile(web)
    new_obs = []
    for token in obs:        
        if len(token)>1 and '-' in token:
            stem_token = stem(token)
            if stem_token not in emit_p['ARTIST'] and \
               stem_token not in emit_p['SONG']:
                if re.search(web_pat, stem_token):
                    new_obs.append(token)
                    continue
                for sub_token in hypen_tokenize(token):
                    new_obs.append(sub_token)
                continue
        new_obs.append(token)
    tokentag_list = punc_tag(new_obs)
    trans_p['EP'] = start_p
    trans_p['EP-'] = start_p
    trans_p['EP&'] = start_p
    record = [{}]
    path = {}
    last_punc = 'EP'
    result = []
    for tokentag in tokentag_list:
        token = tokentag[0]
        tag = tokentag[1]
            
        if last_punc and tag in punc:
            result.append(tag)
            last_punc = tag
        elif last_punc and tag not in punc:
            for state in states:
                prob = trans_p[last_punc].get(state, -100) + \
                       emit_p[state].get(token, -100)
                if state == 'SEP':
                    state = last_punc + '-'
                elif state == 'JOIN':
                    state = last_punc + '&'
                path[state] = [state]
                record[0][state] = prob
            last_punc = False
        elif last_punc is False and tag not in punc:
            newpath = {}
            record.append({})
            for state in states[:-2]:                  
                prob, label = max((emit_p[state].get(token, -100) +
                                   record[-2][s] +
                                   trans_p[s].get(state, -100), s) 
                                   for s in record[-2])
                record[-1][state] = prob
                newpath[state] =  [item for item in path[label]]  
                newpath[state].append(state)
            for state in record[-2]:
                if '&' in state:
                    continue
                prob_sep = emit_p['SEP'].get(token, -100) + \
                           record[-2][state] + \
                           trans_p[state].get('SEP', -100)
                
                state_sep = state.rstrip('[&-]') + '-'
                if prob_sep > record[-1].get(state_sep, -float('inf')):
                    record[-1][state_sep] = prob_sep
                    newpath[state_sep] = [item for item in path[state]]
                    newpath[state_sep].append(state_sep)
            for state in record[-2]:
                if '-' in state:
                    continue
                prob_and = emit_p['JOIN'].get(token, -100) + \
                           record[-2][state] + \
                           trans_p[state].get('JOIN', -100)
                state_and = state.rstrip('[&-]') + '&'
                if prob_and > record[-1].get(state_and, -float('inf')):
                    record[-1][state_and] = prob_and
                    newpath[state_and] = [item for item in path[state]]
                    newpath[state_and].append(state_and)
            path = newpath
        elif last_punc is False and tag in punc:
            last_punc = tag
            newtag = tag
            if tag in end_punc:
                newtag = u'END'
            prob, label = max((record[-1][s] + 
                               trans_p[s].get(newtag, -100), s) 
                               for s in record[-1])
            result += path[label]
            result.append(tag)
            record = [{}]
            path = {}
    if path:
        prob, label = max((record[-1][s] +
                           trans_p[s].get('END', -100), s) 
                           for s in record[-1])
        result += path[label]
    for i, tag in enumerate(result):
        if '-' in tag:
            result[i] = 'SEP'
        elif '&' in tag:
            result[i] = 'JOIN'
    if details:
        print prob
        for item in record:
            print item

    if stemmer == True:
        token_list = [item[0] for item in tokentag_list]
        return zip(token_list, result)
    return zip(new_obs, result)

    

    
#Part of Speach Tagging of YouTube Video title
#info_ind are the list of index of included columns from input 
#data set
#title_id are the index of youtube video title from input data 
def tag_title(inpath, outpath, info_ind, title_ind, stemmer=True):
    states = ['SONG', 'ARTIST', 'OTHER', 'FEAT', 'SEP', 'JOIN']
    with open(inpath, 'rb') as f_read, \
         open(outpath, 'wb') as f_write:
        for line in f_read:
            record = line.decode('utf-8').strip()
            entries = record.split('<SEP>')
            infos = [entries[ind] for ind in info_ind]
            entry = entries[title_ind]
            if entry == 'None' or len(entry) == 0:
                continue
            temp = tokenize(entry)
            tuple_list = viterbi(temp, stemmer=stemmer)
            tokentag_list = [u'<tag>'.join(item)  for item in tuple_list]
            tagging = u'<and>'.join(tokentag_list)
            infos.append(tagging)
            result = u'<SEP>'.join(infos)+'\n'
            f_write.write(result.encode('utf-8'))
            
            
#functions that compute the YouTube video trend
#infile can be something like video0225.txt etc.
def trend(infile1, infile2, field1=1, field2=1,
          write=True):
    view_diff = {}
    previous = {}
    current = {}
    with open(infile1, 'rb') as f1:
        for line in f1:
            record = line.decode('utf-8').strip()
            entries = record.split('<SEP>')
            video = entries[0]
            try:
                entry = int(entries[field1])
            except:
                continue
            previous[video] = entry
    with open(infile2, 'rb') as f2:
        for line in f2:
            record = line.decode('utf-8').strip()
            entries = record.split('<SEP>')
            video = entries[0]
            try:
                entry = int(entries[field2])
            except:
                continue
            current[video] = entry
    for key in previous:
        if key in current:
            view_diff[key] = current[key] - previous[key]
    if write:
        time1 = infile1.rstrip('.txt')[-4:]
        time2 = infile2.rstrip('.txt')[-4:]
        filename = 'trend'+'-'.join([time1, time2])+'.p'
        pickle.dump(view_diff, open(filename, 'wb'))
    return view_diff


#adding language term for a tag SONG or ARTIST
def lang_tag(token, tag):
    cj_scripts = ur'[\u4E00-\u9FFF]|[\u30A0-\u30FF]|[\u3040-\u309F]'
    kr_scripts = ur'[\uAC00-\uD7AF]'
    
    cj_pat = re.compile(cj_scripts)
    kr_pat = re.compile(kr_scripts)
    
    if re.search(cj_pat, token):
        tag += u'_CJ'
    elif re.search(kr_pat, token):
        tag += u'_KR'
    else:
        tag += u'_LA'
    return tag


#standardize token
def normal_token(token):
    special = ur"(?:[\w\u00C0-\u00FF\u0400-\u04FF][/.])+[\w\u00C0-\u00FF\u0400-\u04FF]?"
    ch_scripts = ur'[\u4E00-\u9FFF]' 
    special_pat = re.compile(special)
    ch_pat = re.compile(ch_scripts)
    if re.search(ch_pat, token):
        return ch_stem(token)
    elif re.search(special_pat, token):
        return token.upper()
    elif u'-' in token:
        subtoken_list = hypen_tokenize(token)
        new_list = [subtoken.capitalize() \
                   for subtoken in subtoken_list]
        return ''.join(new_list)
    else:
        return token.capitalize()
            

#process tokentag_list 
#Combine Two songs with JOIN tag as one song
def combine_song(tokentag_list):
    previous_token = None
    previous_tag = u'START'
    total_join = 0
    correction = []
    for i, tokentag in enumerate(tokentag_list):
        token = tokentag[0]
        tag = tokentag[1]
        if previous_tag == 'SONG' and tag == 'JOIN':
            if token == u'&':
                total_join += 1
                correction.append(i)
        elif previous_tag == 'SONG' and tag != 'SONG':
            if total_join == 1:
                total_join -= 1
            elif total_join > 1:
                while total_join > 0:
                    correction.pop()
                    total_join -= 1                
        elif previous_tag == 'JOIN' and tag != 'SONG':
            if len(correction) == 0:
                continue
            if correction[-1] == i - 1:
                total_join -= 1
                temp = correction.pop()
        previous_token = token
        previous_tag = tag
    if correction:
        if i == correction[-1]:
            while total_join > 0:
                correction.pop()
                total_join -= 1
        for ind in correction:
            tokentag_list[ind] = (u'&', 'SONG')
                

#decide if a single token is stopping words
def is_stop(token):
    if token in stop_set:
        return True
    try:
        token = int(token)
        if token != 22:
            return True
    except:
        return False
    

#predictive model to filter out non-music model
def classify(token_list):
    xbeta = 0
    prob = 0
    for token in token_list:
        ind = token_dict.get(token, None)
        if ind:
            xbeta += coef[ind]
    xbeta += coef[-1]
    prob = 1 / (1 + exp(-xbeta))
    if prob >= 0.5:
        return 1
    else:
        return 0


def stem_tokenize(text, simple_token=False):
    web = ur"(?:https?://|www.)[\w\u00C0-\u00FF]+(?:[./?=-][\w\u00C0-\u00FF]+)*[/]?"
    web_pat = re.compile(web)
    new_obs = []
    body = text.split('<newline>')
    title = body[0]
    obs = tokenize(title)
    for item in obs:
        if u'-' in item and len(item) > 6:
            temp = hypen_tokenize(item)
            for token in temp:
                new_obs.append(stem(token))
        else:
            new_obs.append(stem(item))
    for sentence in body[1:]:
        if not sentence:
            continue
        obs = tokenize(sentence, 'nopunc')
        for item in obs:
            if re.search(web_pat, item):
                continue
            if u'-' in item and len(item) > 6:
                temp = hypen_tokenize(item)
                for token in temp:
                    new_obs.append(stem(token))
            else:
                new_obs.append(stem(item))
    if simple_token:
        return new_obs, obs
    return new_obs
    
    
#get artist entity list and song entity list for a youtube video
#source variable can be either
def entity(entry, source='raw', check=False):
    tt = None
    if check:
        new_obs, tt = stem_tokenize(entry, True)
        if classify(new_obs) == 0:
            return 'no music'
    avoid_token = set([',', '，', '.', '。'])
    required = set(['ARTIST', 'SONG'])
    result = {'ARTIST':set(), 'SONG':set()}  
    if entry == u'None':
        return result
    if source == 'intermediate':
        temp_list = entry.split('<and>')
        tokentag_list = [item.split('<tag>') \
                         for item in temp_list \
                         if '<tag>' in item]
    elif source == 'raw':
        if not tt:
            tt = tokenize(entry)
        tokentag_list = viterbi(tt, stemmer=False)
    combine_song(tokentag_list)
    tokentag_list.append((u'None', u'END'))
    current_token = normal_token(tokentag_list[0][0])
    current_tag = tokentag_list[0][1].upper()
    current_tag = lang_tag(current_token, current_tag)
    temp_entity = []
    if current_tag[:-3] in required:
        temp_entity.append(current_token)
    for tokentag in tokentag_list[1:]:
        previous_token = current_token
        previous_tag = current_tag
        current_token = normal_token(tokentag[0])
        current_tag = tokentag[1].upper()
        current_tag = lang_tag(current_token, current_tag)
        if temp_entity and current_tag != previous_tag:
            while temp_entity[-1] in avoid_token:
                temp_entity.pop()
                if not temp_entity:
                    break
            if len(temp_entity) == 1:
                temp = temp_entity[0]
                if is_stop(temp):
                    temp_entity = []
            if previous_tag[-3:] == u'_CJ':
                entity_string = ''.join(temp_entity)
            else:
                entity_string = ' '.join(temp_entity)
            if entity_string:
                result[previous_tag[:-3]].add(entity_string)
            temp_entity = []                    
        if current_tag[:-3] in required:
            temp_entity.append(current_token)
    return result


#combination of elements from two list
def combination(set1, set2):
    if not set1:
        set1.add(u'None')
    if not set2:
        set2.add(u'None')
    result = []
    for item1 in set1:
        for item2 in set2:
            result.append((item1, item2))
    return result


#construct data set of video artist, song name infomation
#in the output data set, there are 7 columns
#Col0. YouTube video ID
#Col1. YouTube vide views increase in the last week
#Col2. Artist  name of this YouTube Video
#Col3, Song name of this YouTube Video
#Col4, Number of artists in this YouTube Video
#Col5, Number of songs in this YouTube Video
#Col6, YouTube video Title
def name_title(trend_dict, infile, outfile, title_ind=4,
               source='raw', check=False):
    with open(infile, 'rb') as f_read, \
         open(outfile, 'wb') as f_write:
        record = []
        for line in f_read:
            line = line.decode('utf-8').strip()
            entries = line.split('<SEP>')
            video = entries[0]
            if video not in trend_dict:
                continue            
            entry = entries[title_ind]
            view_trend = unicode(trend_dict[video])
            meta = entity(entry, source=source, check=check)
            if meta == 'no music':
                continue
            pairs = combination(meta['ARTIST'], meta['SONG'])
            artist_count =unicode(len(meta['ARTIST']))
            song_count = unicode(len(meta['SONG']))
            for pair in pairs:
                obs_list = [video, view_trend, pair[0], pair[1], \
                            artist_count, song_count, entry]
                record.append(u'<SEP>'.join(obs_list)) 
            record_stack = u'\n'.join(record) + u'\n'
            f_write.write(record_stack.encode('utf-8'))
            record = []
                

#Obtain entity trend of YouTube Video titles
#a entity can be an artist name, a song name, or
#an artist-song name pair
#the infile argument should be output of name_title function
def entity_trend(infile, entity_fields, rep_field, 
                 include_id=False, view_field=1):
    if len(entity_fields) > 1:
        rep_field = None
    result = {}
    with open(infile, 'rb') as f:
        for line in f:
            line = line.decode('utf-8').strip()
            entries = line.split('<SEP>')
            entity_list = [entries[field] \
                           for field in entity_fields]
            entity_string = u'<SEP>'.join(entity_list)
            view = float(entries[view_field])
            if include_id:
                video = entries[0]
            try:
                rep = float(entries[rep_field])
            except:
                rep = 1.0
            weight = view / rep
            '''
            values on result dictionary is a list of length 3
            values[0] is total trend last week
            values[1] is the id of the representative youtube
            video id
            values[2] is the trend of the represetative
            youtube video
            
            '''
            if include_id:
                temp = result.get(entity_string, [0, u'None', -float('inf')])
                if view >= temp[2]:
                    temp[1] = video
                    temp[2] = view
            else:
                temp = result.get(entity_string, [0])
            temp[0] += weight
            result[entity_string] = temp
    return result




