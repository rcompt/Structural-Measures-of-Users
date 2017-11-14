# -*- coding: utf-8 -*-
"""
Created on Sat Nov 11 15:23:48 2017

@author: James
"""

import os
import csv

import networkx as nx
import re


def recursive_reply_count(post,post_count,titles):
    replies = titles[(post["title"].replace(" ",""),post["post_id"])]["replies"]
    if post["email"] not in post_count:
        post_count[post["email"]] = 1
    else:
        post_count[post["email"]] += 1
    if len(replies) > 0:
        for reply_2 in replies:
            post_count = recursive_reply_count(reply_2,post_count,titles)
    return post_count

comm = "1a497c6f-915d-4a3d-81fe-cbbccec3eabe"

#Store directories to data 
text_dir = "C:\\Users\\James\\Google Drive\\Grad Research\\Links\\2000 communities\\commtext_clean"
link_dir = "C:\\Users\\James\\Google Drive\\Grad Research\\Links\\2000 communities\\DATA-links-anonymous-2000c-20140601\\links-out"
user_dir = "C:\\Users\\James\\Google Drive\\Grad Research\\Links\\2000 communities\\DATA-members-anonymous-2000c-20140514\\out"

#Only examine this list of tools
tools = ["Blog","BlogCmt","Forum","ForumRep"]

#Gather Associated Data Files
text_file = open(os.path.join(text_dir,comm),"rb")
link_file = open(os.path.join(link_dir,"links-"+comm+".csv"),"rb")
user_file = open(os.path.join(user_dir,comm+"-members.csv"),"rb")

#Dictionaries for tool specific post information
blog_title = {}
forum_title = {}
blog = {}
blogcmt = {}
forum = {}
forumrep = {}

#Initialize graph and user dictionary
comm_graph = nx.Graph()
comm_users = {}    

#Read the users within a community
reader = csv.DictReader(user_file)
for row in reader:
    comm_users[row["email"]] = {}
    comm_users[row["email"]]["comm_role"] = row["comm_role"]
    comm_users[row["email"]]["text"] = ""
    comm_users[row["email"]]["links"] = 0
    comm_users[row["email"]]["posts"] = 0
    comm_users[row["email"]]["posts_text"] = {}

#Set up user reference dictionary and add user to graph
i = 0
comm_reference = {}
for uid in comm_users.keys():
    comm_graph.add_node(i, email=uid, role =comm_users[uid]["comm_role"] )
    comm_reference[uid] = i
    i = i+1    

user_file.close()

#Set up error file
error_file = open(comm + "_Error_Log.txt","w")

#hold all text in community
comm_text = ""
#Create sequential post id
post_id = 1

#Open csv file, no headers are expected
reader = csv.reader(text_file)
#Set up recent post to reference original post of a comment or reply
recent_forum_title = ""
recent_blog_title = ""
previous_initial = {}
previous_reply = {}
title_id = ""
#iterate through csv file
for row in reader:
    #Gather post information and text
    author = row[0]
    tool = row[3]
    title = row[4].rstrip()
    text = row[5].replace(title,"")
    depth = len(re.findall("Re: ",title))
    #Information depth found if greater than 1
    #Debug statement
    if depth > 1:
        print("Found depth of %s" % depth)
        print("In Comm: %s" % comm)
        print("Line: %s" % post_id)
    #Check that we are only looking at tools of interest
    if tool in tools:
        #Remove extra whitespace
        title_id = " ".join(title.split())
        #Store post data within appropriate dictionary
        if tool == 'Blog':
            blog_title[title_id,post_id] = {}
            blog_title[title_id,post_id]['initial'] = {'email': author, 'text': text, 'title': title, 'post_id': post_id}
            blog_title[title_id,post_id]['replies'] = []
        #If tool is a Blog Comment, then an original post must be found
        elif tool == 'BlogCmt' and "Re:" in title:
            blog_title[title_id,post_id] = {}
            blog_title[title_id,post_id]['initial'] = {'email': author, 'text': text, 'title': title, 'post_id': post_id}
            blog_title[title_id,post_id]['replies'] = []
            #If original post is found then store this post within the replies of that original post
            if (title_id[3:],previous_initial["post_id"]) in blog_title:
                blog_title[title_id[3:],previous_initial["post_id"]]['replies'].append({'email': author, 'text': text, 'title': title, 'post_id': post_id})
            #If the original post is also a comment, then look at the previous reply
            elif "Re:" in title_id[3:]:
                blog_title[title_id[3:],previous_reply["post_id"]]['replies'].append({'email': author, 'text': text, 'title': title, 'post_id': post_id})
            #If no previous post or reply is found, then log this in the error file
            else:
                error_file.write(str(comm)+","+str(post_id)+","+str(tool)+","+str(title)+","+str(title_id[3:])+"\n")
                continue
        #Repeat same logic above for blogs for forums
        elif tool == 'Forum':
            forum_title[title_id,post_id] = {}
            forum_title[title_id,post_id]['initial'] = {'email': author, 'text': text, 'title': title, 'post_id': post_id}
            forum_title[title_id,post_id]['replies'] = []
        elif tool == 'ForumRep' and "Re:" in title:
            forum_title[title_id,post_id] = {}
            forum_title[title_id,post_id]['initial'] = {'email': author, 'text': text, 'title': title, 'post_id': post_id}
            forum_title[title_id,post_id]['replies'] = []
            if (title_id[3:],previous_initial["post_id"]) in forum_title:
                forum_title[title_id[3:],previous_initial["post_id"]]['replies'].append({'email': author, 'text': text, 'title': title, 'post_id': post_id})
            elif "Re:" in title_id[3:] and (title_id[3:],previous_reply["post_id"]) in forum_title:
                forum_title[title_id[3:],previous_reply["post_id"]]['replies'].append({'email': author, 'text': text, 'title': title, 'post_id': post_id})
            else:
                error_file.write(str(comm)+","+str(post_id)+","+str(tool)+","+str(title)+","+str(title_id[3:])+"\n")
                continue
        #Gather all community text
        #Used for linguistic measures, not used in current test
        comm_text += text + " "
        #Set post to be assumed false at first
        response = False
        op = "self"
        #If post is a reply, then find the OP
        if tool in ["BlogCmt","ForumRep"] and "Re: " in title:
            response = True
            if depth > 1:
                op = previous_reply["email"]
            else:
                op = previous_initial["email"]
        #Add post information to comm_user dictionary
        if author in comm_users:
            comm_users[author]["text"] += text + " "
            comm_users[author]["posts"] += 1
            comm_users[author]["posts_text"][post_id] = {
                                                            "text":text,
                                                            "title":title,
                                                            "repsonse": response,
                                                            "OP": op
                                                        }
        #If author is not listed from the user data, then create entry for them
        else:
            comm_users[author] = {}
            comm_users[author]["text"] = text + " "
            comm_users[author]["comm_role"] = "unknown"
            comm_users[author]["links"] = 0
            comm_users[author]["posts"] = 1
            comm_users[author]["posts_text"] = {}
            comm_users[author]["posts_text"][post_id] = {
                                                            "text":text,
                                                            "title":title,
                                                            "response": response,
                                                            "OP": op
                                                        }
            comm_reference[author] = len(comm_reference.keys())
            comm_graph.add_node(i, email=uid, role ='unknown' )
        #If the OP is not the same as the current post's author
        #Then add an edge within the graph
        if tool in ["BlogCmt","ForumRep"] and "Re: " in title:
            if author != op:
                comm_graph.add_edge(comm_reference[author], comm_reference[op])
    #Set previous reply or initial post based on the depth
    if depth > 0:
        previous_reply = {'email': author, 'text': text, 'title': title, 'post_id': post_id}
    else:
        previous_initial = {'email': author, 'text': text, 'title': title, 'post_id': post_id}
    post_id += 1

text_file.close()

#Find structural metrics per user

#creating analytics for this section
#avg in degree (for both members and leaders
degree = nx.degree_centrality(comm_graph)
for k, v in degree.items():
    comm_graph.node[k]['degree'] = str(v)
    if comm_graph.node[k]['role'] == 'member':
        if v > 0 :
            print ' Degree: member', v
    if 'owner' in comm_graph.node[k]:
        if v > 0:
            print 'Degree: Owner' , v

#clustering coefficient
#general
cluster =nx.clustering(comm_graph)
for k, v in cluster.items():
    comm_graph.node[k]['clustering'] = str(v)
    if comm_graph.node[k]['role'] == 'member':
        if v > 0 :
            print 'Clustering: member', v
    if 'owner' in comm_graph.node[k]:
        if v > 0:
            print 'Clustering: owner' , v
#for particular nodes


#triads
triangle = nx.triangles(comm_graph)

for k, v in triangle.items():
    comm_graph.node[k]['triangle'] = str(v)
    if comm_graph.node[k]['role'] == 'member':
        if v > 0:
            print 'Triangle: member', v
    if 'owner' in comm_graph.node[k]:
        if v > 0:
            print 'Triangle: owner', v

#k-core

core = nx.core_number(comm_graph)
for k, v in core.items():
    comm_graph.node[k]['core']= str(v)
    if v > 0:
        print 'Core:'
        print k,v

#diameter

#centrality (betweeness centrality)
between = nx.betweenness_centrality(comm_graph)
for k,v in between.items():
    comm_graph.node[k]['centrality'] = str(v)
    if v >0:
        print k, v

#Boundary Span, found through dividing the number of unique threads
#a user posts in by the number of total posts they make
boundarySpan = {}
for user in comm_users:
    boundarySpan[user] = {
                            'unique': 0,
                            'posts': 0
                        }
post_count = {}
#Find the boundary span for each type of tool
for title,pid in [(x,y) for (x,y) in forum_title if "Re:" not in x]:
    post_count = recursive_reply_count(forum_title[(title,pid)]["initial"],post_count,forum_title)
    for user in post_count:
        boundarySpan[user]['unique'] += 1
        boundarySpan[user]['posts'] += post_count[user]
    post_count = {}
for title,pid in [(x,y) for (x,y) in blog_title if "Re:" not in x]:
    post_count = recursive_reply_count(blog_title[(title,pid)]["initial"],post_count,blog_title)
    for user in post_count:
        boundarySpan[user]['unique'] += 1
        boundarySpan[user]['posts'] += post_count[user]
    post_count = {}

#Set up outfile directory if not already existing
out_dir = "Analytics Per Comm"
if out_dir not in os.listdir(os.getcwd()):
    os.mkdir(os.path.join(os.getcwd(),out_dir))

#write new metrics to outfile
with open(os.path.join(out_dir,comm+'.csv'), 'wb') as outfile:
    writer = csv.writer(outfile)
    # write header
    headers = ["email","role","posts","readability","unique_words","sentiment","proto-typical","boundary-span","links","clustering","core","centrality","degree","triangle"]
    writer.writerow(headers)
    # write data
    i = 0
    for cur_author in comm_users:
       # print G1.node[data]
       data = comm_reference[cur_author]
       if data in comm_graph.node:
           new_row = []
           new_row.append(cur_author)
           if 'comm_role' not in comm_users[cur_author]:
               new_row.append("unknown")
           else:
               new_row.append(comm_users[cur_author]['comm_role'])
           new_row.append(comm_users[cur_author]["posts"])
           new_row.append(comm_users[cur_author]["Readability"])
           new_row.append(comm_users[cur_author]["Unique Words"])
           new_row.append(comm_users[cur_author]["Sentiment"])
           new_row.append(comm_users[cur_author]["proto-typical"])
           new_row.append(comm_users[cur_author]["boundary-span"])
           new_row.append(comm_users[cur_author]["links"])
           if data not in comm_users:
               new_row.append("0")
               new_row.append("0")
               new_row.append("0")
               new_row.append("0")
               new_row.append("0")
           else:
               if 'clustering' not in comm_users[data]:
                   new_row.append("0")
               else:
                   new_row.append(comm_graph.node[data]['clustering'])
               if 'core' not in comm_users[data]:
                   new_row.append("0")
               else:
                   new_row.append(comm_graph.node[data]['core'])
               if 'centrality' not in comm_users[data]:
                   new_row.append("0")
               else:
                   new_row.append(comm_graph.node[data]['centrality'])       
               if 'degree' not in comm_users[data]:
                   new_row.append("0")
               else:
                   new_row.append(comm_graph.node[data]['degree'])       
               if 'triangle' not in comm_users[data]:
                   new_row.append("0")
               else:
                   new_row.append(comm_graph.node[data]['triangle'])                               
           writer.writerow(new_row)


