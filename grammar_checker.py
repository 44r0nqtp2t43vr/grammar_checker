import nltk
nltk.download('brown')

from nltk.corpus import brown
from itertools import chain

all_brown_tagged_words = list(set(chain.from_iterable(brown.tagged_sents())))

complex_tags = ['+', '-', '*', ':']
all_brown_tagged_words = [pair for pair in all_brown_tagged_words if not (any(map(pair[1].__contains__, ['+', '-', '*', ':', ',', '(', ')', '\'', '`', '.'])))]
all_brown_tags = list(set([item[1] for item in all_brown_tagged_words]))

lexicon_dict = {}
for tag in all_brown_tags:
    # if tag == 'NP':
    #     lexicon_dict['NPR'] = list(set([pair[0].upper() for pair in all_brown_tagged_words if pair[1] == tag]))
    #     continue
    lexicon_dict[tag] = list(set([pair[0].upper() for pair in all_brown_tagged_words if pair[1] == tag]))

lexicon_dict['PN'] = lexicon_dict['PN'] + ['ALL']
lexicon_dict['VB'] = lexicon_dict['VB'] + ['BOOK']
lexicon_dict['NP'] = [word for word in lexicon_dict['NP'] if word not in ['MY']]

# grammar_dict = {
#     'S': [['NP', 'VP']],
#     'NP': [['AT', 'NN'], ['AT', 'NNS']],
#     'VP': [['VB', 'NR'], ['VBD', 'NR'], ['VBZ', 'NR'], ['MD', 'VB', 'NR']]
# }
grammar_dict = {
    'S': [['XVP'], ['NPVP'], ['NPVP', 'CC', 'NPVP'], ['NPVP', 'CS', 'NPVP'], ['SAUX', 'SNP', 'VB', 'OBJ'], ['PAUX', 'PNP', 'VB', 'OBJ']],
    'XVP': [['VB'], ['VB', 'XOBJ'], ['VB', 'RB'], ['VB', 'XOBJ', 'RB'], ['VB', 'XOBJ', 'PP']],
    'NPVP': [['SNP', 'SVP'], ['PNP', 'PVP'], ['SNP', 'SVP', 'PP'], ['PNP', 'PVP', 'PP']],
    'SNP': [['NN'], ['SAT', 'NN'], ['NP'], ['SAT', 'NP'], ['PPS']],
    'SVP': [['SVB'], ['SVB', 'RB'], ['SVB', 'NR'], ['SVB', 'OBJ'], ['SVB', 'OBJ', 'RB']],
    'SVB': [['VBD'], ['VBZ'], ['MD', 'VB']],
    'SAUX': [['DOD'], ['DOZ'], ['MD']],
    'SAT': [['AT'], ['DT'], ['PP$']],
    'PNP': [['NNS'], ['PAT', 'NNS'], ['NPS'], ['PAT', 'NPS'], ['PPSS']],
    'PVP': [['PVB'], ['PVB', 'RB'], ['PVB', 'NR'], ['PVB', 'OBJ'], ['PVB', 'OBJ', 'RB']],
    'PVB': [['VBD'], ['VB'], ['MD', 'VB']],
    'PAUX': [['DOD'], ['DO'], ['MD']],
    'PAT': [['AT'], ['DTS'], ['PP$']],
    'OBJ': [['PPO'], ['NNS'], ['NP'], ['AT', 'NN'], ['AT', 'NNS'], ['AT', 'NP']],
    'XOBJ': [['AT', 'NN'], ['DT', 'NN'], ['NNS'], ['AT', 'NNS'], ['DTS', 'NNS'], ['NP'], ['AT', 'NP'], ['DT', 'NP']],
    'PP': [['IN', 'PN'], ['IN', 'SAT', 'NN'], ['IN', 'PAT', 'NNS']],
}

row_id = 0

class EarleyRow:
    def __init__(self, pid, chart, operator, start, end, symbol, production, cid = None):
        global row_id
        self.id = row_id
        row_id = row_id + 1
        self.pid = pid
        self.chart = chart
        self.operator = operator
        self.start = start
        self.end = end
        self.symbol = symbol
        self.production = production
        self.cid = cid
    
    def print_row(self):
        print(self.chart, self.id, self.pid, self.operator, self.start, self.end, self.symbol, self.production, self.cid)

class EarleyParser:
    def __init__(self, lexicon, grammar):
        self.lexicon = lexicon
        self.grammar = grammar
        self.terminals = [key for key in lexicon]
        self.nonterminals = [key for key in grammar]
        self.parsed = []

    def shift_dot(self, prod):
        if '*' in prod:
            index = prod.index('*')
            prod.remove('*')
            prod.insert(index + 1, '*')
            return prod

    def predict(self, earley_row):
        prod = getattr(earley_row, 'production')
        for child_prod in self.grammar[prod[prod.index('*') + 1]]:
            pid = getattr(earley_row, 'id') # parent id
            chart = getattr(earley_row, 'chart')
            end = getattr(earley_row, 'end')
            symbol = prod[prod.index('*') + 1]
            child_row = EarleyRow(pid, chart, 'PRED', end, end, symbol, ['*'] + child_prod)
            self.table.append(child_row)
            cr_prod = getattr(child_row, 'production')
            if cr_prod[cr_prod.index('*') + 1] in self.terminals:
                continue
            self.predict(child_row)
    
    def scan(self, earley_row, word):
        prod = getattr(earley_row, 'production')
        if word.upper() in self.lexicon[prod[prod.index('*') + 1]]:
            pid = getattr(earley_row, 'id')
            chart = getattr(earley_row, 'chart') + 1
            start = getattr(earley_row, 'start')
            end = getattr(earley_row, 'end') + 1
            symbol = prod[prod.index('*') + 1]
            self.table.append(EarleyRow(pid, chart, 'SCAN', start, end, symbol, [word, '*']))
            return True
        return False
    
    def complete(self, to_comp_row, comp_row):
        comp_symbol = getattr(comp_row, 'symbol')
        comp_prod = getattr(comp_row, 'production')
        while comp_symbol != 'S' and comp_prod[-1] == '*':
            last_cid = getattr(to_comp_row, 'cid')
            if last_cid != None:
                cid = [getattr(comp_row, 'id')] + last_cid
            else:
                cid = [getattr(comp_row, 'id')] + [last_cid]
            pid = getattr(to_comp_row, 'pid')
            chart = getattr(comp_row, 'chart')
            start = getattr(to_comp_row, 'start')
            end = getattr(comp_row, 'end')
            symbol = getattr(to_comp_row, 'symbol')
            prod = getattr(to_comp_row, 'production').copy()
            comp_row = EarleyRow(pid, chart, 'COMP', start, end, symbol, self.shift_dot(prod), cid)
            self.table.append(comp_row)
            comp_symbol = getattr(comp_row, 'symbol')
            comp_prod = getattr(comp_row, 'production')
            to_comp_row = ([row for row in self.table if row.id == pid])[0]
            
    
    def parse(self, sentence):
        sentence = sentence.split()
        self.table = [EarleyRow(0, 0, 'PRED', 0, 0, 'y', ['*', 'S'])]
        self.predict(self.table[0])
        for index, word in enumerate(sentence):
            to_scan = [er for er in self.table if getattr(er, 'chart') == index and (getattr(er, 'production')[-1] != '*' and getattr(er, 'production')[getattr(er, 'production').index('*') + 1] in self.terminals)]
            for row in to_scan:
                has_scanned = self.scan(row, word)
                if has_scanned:
                    self.complete(row, self.table[-1])
                    comp_prod = getattr(self.table[-1], 'production')
                    comp_symbol = getattr(self.table[-1], 'symbol')
                    if  index == len(sentence) - 1 and (comp_symbol == 'S' and comp_prod[-1] == '*'):
                        break
                    if comp_prod[-1] != '*' and comp_prod[comp_prod.index('*') + 1] not in self.terminals:
                        self.predict(self.table[-1])
        for row in self.table:
            row.print_row()
        if getattr(self.table[-1], 'symbol') == 'S' and getattr(self.table[-1], 'production')[-1] == '*':
            return True
        return False
    
    def get_parsed(self, to_get = None):
        if self.table == None:
            return
        if to_get == None:
            to_get = self.table[-1]
        to_get_cid = getattr(to_get, 'cid')
        if to_get_cid == None:
            self.parsed.append(to_get)
            to_get.print_row()
            return
        for cid in to_get_cid:
            if cid == None:
                self.parsed.append(to_get)
                to_get.print_row()
                return
            next_row = ([row for row in self.table if getattr(row, 'id') == cid])[0]
            self.get_parsed(next_row)
        

line = 'the boy went home'
# line = 'the boy go home'
# line = 'the boys went home'
# line = 'the boy goes home'
# line = 'the boys go home'
# line = 'the boy will go home'
# line = 'the boys will go home'
# line = 'the boys will go home safely'

# line = 'i love you'
# line = 'i loved you'
# line = 'i will love you'
# line = 'he loves you'
# line = 'he loved you'
# line = 'he will love you'

# line = 'i love you dearly'
# line = 'i loved you dearly'
# line = 'i will love you dearly'
# line = 'he loves you dearly'
# line = 'he loved you dearly'
# line = 'he will love you dearly'

# line = 'do you love me too'
# line = 'did you love me too'
# line = 'will you love me too'
# line = 'does the boy go home safely'
# line = 'did the boy went home safely'
# line = 'will the boy go home safely'

# line = 'love God'
# line = 'love dogs'
# line = 'love the boy'
# line = 'love God above all'
# line = 'love dogs above all'
# line = 'love the boy above all'
# line = 'love the boy dearly'

# line = 'love'
# line = 'love dearly'
# line = 'love hurts'
# line = 'love hurt'
# line = 'love will hurt'
# line = 'love will hurt dearly'

# line = 'i love you but you love him'
# line = 'i loved you but you loved him'
# line = 'i loved you dearly but the boy went home safely'
# line = 'i love you because you love him'
# line = 'i loved you because you loved him'
# line = 'i loved you dearly since the boy went home safely'

# line = 'i love God'
# line = 'i love the boy'
# line = 'she loves the boy'
# line = 'she loves boys'
# line = 'she loves the boys'

# line = 'book that flight'
# line = 'book those flights'
# line = 'my boy went home'
# line = 'Julie went home'
# line = 'that boy went home'
# line = 'those boys went home'
# line = 'i loved you above all'
# line = 'i love you in the house'
# line = 'i love you in my house'
# line = 'i will love you above all but you loved him above all'

# line = 'the boy shoots the bird in his pajamas'

# for word in line.split():
#     print(word, [tag for tag in lexicon_dict if word.upper() in lexicon_dict[tag]])

parser = EarleyParser(lexicon_dict, grammar_dict)
if parser.parse(line):
    print('\nThe sentence is grammatically correct')
    parser.get_parsed()
    print([getattr(row, 'symbol') for row in getattr(parser, 'parsed')])
else:
    print('\nThe sentence is grammatically incorrect')


# with open('tags.txt', 'w') as fp:
#     for tag in lexicon_dict:
#         fp.write(tag + "\t" + str(len(lexicon_dict[tag])) + "\n")

# with open('lexicon.txt', 'w') as fp:
#     for tag in lexicon_dict:
#         fp.write("%s\n" % tag)
#         for word in lexicon_dict[tag]:
#             fp.write("%s " % word)
#         fp.write("\n")

# with open('nn.txt', 'w') as fp:
#     for word in lexicon_dict['NN']:
#         fp.write("%s " % word)