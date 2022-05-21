from bs4 import BeautifulSoup
import bs4
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import os

import json

import sys
import argparse
import threading

from yaml import parse

argparser = argparse.ArgumentParser()
argparser.add_argument('page', help='imported page of folder')
#argparser.add_argument('--r', dest='r', action='store_true')
args = argparser.parse_args()

PagePath = args.page
#FOR TEST
#PagePath = 'page.html'

parsed_page = None
parsed_pages = None


with open(PagePath) as file:
    try:
        parsed_page = BeautifulSoup(file, 'html.parser')
    except:
        print('selected file is not an html page')
        print('exiting..')
        exit()

#dict of configs
Config = None
with open('config.json', 'r') as file:
    Config = json.load(file)


class StructureOrganiser:
    def __init__(self):
        self.tagsVector = None

    def add_tagsvector(self, tagsVector):
        self.tagsVector = tagsVector

    class TagsVector:
        def __init__(self, tags, block, inline):
            self.structure = tags
            self.block_structure = block
            self.inline_structure = inline


class Block:
    class Exceptions(Exception):
        class ArgumentException(Exception):
            pass
    def __init__(self, me, page, parent, rec=None, args=None):
        #bs4..Tag
        self.page = page
        #bs4..Tag
        self.me = me
        #Block
        self.parent = parent
        #Block
        self.children = []
        if rec != None:
            if args == None:
                raise self.Exceptions.ArgumentException('Block init arguments expected')
            rec(self, args)
        #children - children blocks
        #self.children = 
        self.characteristic = None

    def add_characteristic(self, structureOrganiser):
        self.characteristic = CharacteristicBlock(structureOrganiser, self.me, self.page, self.parent, self.children)
    def add_parent(self, blocks):
        try:
            self.parent = blocks[hash(self.me.parent)]
        except:
            with open('output.out', 'w') as file:
                file.write(str(self.me) + '\n' + '='*100 + '\n')
            print('0')

class CharacteristicBlock(Block):
    class TagVector:
        def __init__(self, block, inline, all):
            self.block = block
            self.inline = inline
            self.all = all

    def __init__(self, structureOrganiser, me, page, parent, children):
        super().__init__(me, page, parent)
        #tags - dict {tagname:iterators}
        #self.tags = tags
        self.children = children
        self.structureOrganiser = structureOrganiser
        self.firstorder_tagvector = None
        self.full_tagvector = None

    #finding blocks that have the same structure
    def get_similars(self, Blocks):
        firstorder_tagvector = self.get_firstorderTagvector()
        full_tagvector = self.get_fullTagvector()

        similarby_fo = []
        similarby_full = []

        for block in Blocks.items():
            if np.array_equal(block[1].characteristic.get_firstorderTagvector(), firstorder_tagvector):
                similarby_fo.append(block[0])
            if np.array_equal(block[1].characteristic.get_fullTagvector(), full_tagvector):
                similarby_full.append(block[0])
        return (similarby_fo, similarby_full)
    
    def compare_structures(self, Block1, Block2=None):
        if Block2 == None:
            Block2 = self
        if Block1.me.name == Block2.me.name:
            if len(Block1.children) == len(Block2.children):
                    flag = True
                    for i in range(len(Block1.children)):
                        flag = flag and self.compare_structures(Block1.children[i], Block2.children[i])
                    return flag
        return False
        

    def get_similars_structure(self, Blocks):
        similar = []
        for block in Blocks.items():
            if self.compare_structures(block[1]):
                similar.append(block[0])
        return similar
    
    #finding blocks that have structure close to self block
    def get_close(self, Blocks, Config):
        firstorder_tagvector = self.get_firstorderTagvector()
        full_tagvector = self.get_fullTagvector()

        closeby_fo = []
        closeby_full = []

        relativeTolerance = 10**(-5)
        absoluteTolerance = 10**(-8)
        if Config['analysis']['closeblocks_relativeTolerance'] >= 0:
            relativeTolerance = Config['analysis']['closeblocks_relativeTolerance']
        if Config['analysis']['closeblocks_absoluteTolerance'] >= 0:
            absoluteTolerance = Config['analysis']['closeblocks_absoluteTolerance']

        for block in Blocks.items():
            if np.allclose(firstorder_tagvector, block[1].characteristic.get_firstorderTagvector(), relativeTolerance, absoluteTolerance):
                closeby_fo.append(block[0])
            if np.allclose(full_tagvector, block[1].characteristic.get_fullTagvector(), relativeTolerance, absoluteTolerance):
                closeby_full.append(block[0])
        
    def calculate(self):
        return
    
    def get_firstorderTagvector(self, tagtype='all'):
        def fill_tagvector(structure):
            tag_vector = np.zeros(len(structure))
            if self.me.children != None:
                for child in self.me.children:
                    if child.name in structure:
                        tag_vector[structure.index(child.name)] += 1
            return tag_vector
        def ret(tagtype):
            if tagtype == 'all':
                return self.firstorder_tagvector.all
            elif tagtype == 'block':
                return self.firstorder_tagvector.block
            elif tagtype == 'inline':
                return self.firstorder_tagvector.inline
            else:
                raise ValueError(tagtype)

        if self.firstorder_tagvector != None:
            return ret(tagtype)
        self.firstorder_tagvector = self.TagVector(
            fill_tagvector(self.structureOrganiser.tagsVector.block_structure),
            fill_tagvector(self.structureOrganiser.tagsVector.inline_structure),
            fill_tagvector(self.structureOrganiser.tagsVector.structure)
        )
        return ret(tagtype)
    def get_fullTagvector(self, tagtype='all'):
        def fill_tagvector(structure):
            tag_vector = np.zeros(len(structure))
            for tag in structure:
                if self.me.find_all(tag) != None:
                    for tg in self.me.find_all(tag):
                        if tg.name in structure:
                            tag_vector[structure.index(tg.name)] += 1
            return tag_vector
        def ret(tagtype):
            if tagtype == 'all':
                return self.full_tagvector.all
            elif tagtype == 'block':
                return self.full_tagvector.block
            elif tagtype == 'inline':
                return self.full_tagvector.inline
            else:
                raise ValueError(tagtype)

        if self.full_tagvector != None:
            return ret(tagtype)
        self.full_tagvector = self.TagVector(
            fill_tagvector(self.structureOrganiser.tagsVector.block_structure),
            fill_tagvector(self.structureOrganiser.tagsVector.inline_structure),
            fill_tagvector(self.structureOrganiser.tagsVector.structure)
        )
        return ret(tagtype)
    

    def firstorder_fullness(self, tagtype='all'):
        return np.linalg.norm(self.get_firstorderTagvector(tagtype))
    def fullness(self, tagtype='all'):
        return np.linalg.norm(self.get_fullTagvector(tagtype))

    def graph(self, plt, Config, order='all'):
        def plot(fig, tag_vector, tag_names, graphname):
            plt = fig.add_subplot()
            #plt.scatter(np.arange(len(tag_vector)), tag_vector)
            zeros = []
            for i in range(len(tag_vector)):
                if tag_vector[i] == 0:
                    zeros.append(i)
            tag_vector = np.delete(tag_vector, zeros)
            tag_names = np.delete(tag_names, zeros)
            def make_legend():
                persentages = [tag*100 / sum(tag_vector) for tag in tag_vector]
                max_length_name = len(max(tag_names, key=len))
                max_length_tag = len(max([str(tag) for tag in tag_vector], key=len))
                legend = [
                        tag_names[i] +
                        ' '*(max_length_name - len(tag_names[i]) + 1) +
                        str(int(tag_vector[i])) +
                        ' '*(max_length_tag - len(str(tag_vector[i])) + 1) +
                        "({:.2f}%)".format(persentages[i]) for i in range(len(tag_vector))
                    ]
                return legend
            fig.suptitle(graphname)
            counter = [0]
            def format_pct(pct, counter):
                string = ''
                if pct >= 2:
                    string = "{:s}\n{:.3f}%".format(tag_names[counter[0]], pct)
                counter[0] += 1
                return string
            plt.pie(
                tag_vector, autopct=lambda pct: format_pct(pct, counter), radius = 1.5)
            plt.legend(
                bbox_to_anchor = (-0.5, 0.5, 0.25, 0.25),
                loc = 'lower left', labels = make_legend())

        def firstorder_tagvector(plt, graphConfig):
            fig1 = plt.figure(figsize=(graphConfig["size_x"], graphConfig["size_y"]))
            fig2 = plt.figure(figsize=(graphConfig["size_x"], graphConfig["size_y"]))
            fig3 = plt.figure(figsize=(graphConfig["size_x"], graphConfig["size_y"]))
            plot(fig1, self.get_firstorderTagvector(tagtype='block'), self.structureOrganiser.tagsVector.block_structure, 'firstorder_block')
            plot(fig2, self.get_firstorderTagvector(tagtype='inline'), self.structureOrganiser.tagsVector.inline_structure, 'firstorder_inline')
            plot(fig3, self.get_firstorderTagvector(tagtype='all'), self.structureOrganiser.tagsVector.structure, 'firstorder_all')
            return (fig1, fig2, fig3)
        #TOCORRECT
        def full_tagvector(plt, graphConfig):
            fig1 = plt.figure(figsize=(graphConfig["size_x"], graphConfig["size_y"]))
            fig2 = plt.figure(figsize=(graphConfig["size_x"], graphConfig["size_y"]))
            fig3 = plt.figure(figsize=(graphConfig["size_x"], graphConfig["size_y"]))
            plot(fig1, self.get_fullTagvector(tagtype='block'), self.structureOrganiser.tagsVector.block_structure, 'full_block')
            plot(fig2, self.get_fullTagvector(tagtype='inline'), self.structureOrganiser.tagsVector.inline_structure, 'full_inline')
            plot(fig3, self.get_fullTagvector(tagtype='all'), self.structureOrganiser.tagsVector.structure, 'full_all')
            return (fig1, fig2, fig3)

        graphConfig = Config["appearance"]["graph"]

        plt.rc('font', family=graphConfig["axis"]["fontfamily"])
        #plt.xlabel('tags', fontsize=graphConfig["axis"]["fontsize"])
        #plt.ylabel('amount', fontsize=graphConfig["axis"]["fontsize"])

        if order == 'all':
            return (firstorder_tagvector(plt, graphConfig), full_tagvector(plt, graphConfig))
        elif order == 'first':
            return firstorder_tagvector(plt, graphConfig)
        elif order == 'full':
            return full_tagvector(plt, graphConfig)


#class CharacteristicPage(CharacteristicBlock):


def init_StructureOrganiser(config):
    structureOrganiser = StructureOrganiser()
    structureOrganiser.add_tagsvector(StructureOrganiser.TagsVector(
            config['tags']['block'] + config['tags']['inline'],
            config['tags']['block'],
            config['tags']['inline'])
        )
    return structureOrganiser






#dict of all blocks in page
structureOrganiser = init_StructureOrganiser(Config)

#args: {Blocks dict, page, }
def CreateBlock(block, args):
    args['Blocks'].update({hash(block.me) : block})
    if isinstance(block.me, bs4.element.Tag):
        for blk in block.me.children:
            if isinstance(blk, bs4.element.Tag) and blk.children != None:
                #args['Blocks'].update({hash(blk) : Block(blk, args['Page'], args['Blocks'][hash(block.me)], CreateBlock, args)})
                Block(blk, args['Page'], args['Blocks'][hash(block.me)], CreateBlock, args)
                block.children.append(args['Blocks'][hash(blk)])

Blocks = {}
Block(parsed_page.body, parsed_page, None, CreateBlock, {'Blocks' : Blocks, 'Page' : parsed_page})

for block in Blocks.values():
    block.add_characteristic(structureOrganiser)

print(len(Blocks))


for block in Blocks.values():
    block.add_characteristic(structureOrganiser)

def find_similar(Blocks):
    sims = []
    _Blocks = Blocks.copy()

    def similars(_Blocks, lst):
        key, block = random.choice(list(_Blocks.items()))
        sims = block.characteristic.get_similars(_Blocks)[1]
        if sims == [key]:
            _Blocks.pop(key)
        else:
            lst.append(sims)
            for sim in lst[-1]:
                _Blocks.pop(sim)
        if len(_Blocks) != 0:
            similars(_Blocks, lst)

    similars(_Blocks, sims)

    similars_str = ''
    for sim in sims:
        similars_str += str(sim) + '\n'
    with open('similars.txt', 'w') as file:
        file.write(similars_str)

def find_similar_structures(Blocks):
    sims = []
    _Blocks = Blocks.copy()
    def similars_structure(_Blocks, lst):
        key, block = random.choice(list(_Blocks.items()))
        sims = block.characteristic.get_similars_structure(_Blocks)
        if sims == [key]:
            _Blocks.pop(key)
        else:
            lst.append(sims)
            for sim in lst[-1]:
                _Blocks.pop(sim)
        if len(_Blocks) != 0:
            similars_structure(_Blocks, lst)

    similars_structure(_Blocks, sims)

    sims_source = []
    for sim in sims:
        #print(sim)
        sims_source.append([(Blocks[s].me.sourceline, Blocks[s].me.sourcepos) for s in sim])
    similars_structure_str = ''
    for sim in sims_source:
        similars_structure_str += str(sim) + '\n'
    with open('similar_structures.txt', 'w') as file:
        file.write(similars_structure_str)

def graph_body(parsed_page, Blocks):
    body = parsed_page.body
    bodyBlock = Blocks[hash(body)]
    bodyBlock.characteristic.graph(plt, Config, 'all')
    for i in plt.get_fignums():
        plt.figure(i).savefig(f'./pics/{i}')

find_similar(Blocks)
find_similar_structures(Blocks)
graph_body(parsed_page, Blocks)

def ComparePages(pages, Config, structureOrganiser):
    Bodies = {}
    for page in pages:
        Bodies.update({hash(page.body) : Block(page.body, page, None)})
    for body in Bodies:
        body.add_characteristic(structureOrganiser)
    
